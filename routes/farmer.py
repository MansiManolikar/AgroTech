from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db
from helpers import log_action
from mongo_db import (
    save_weather,
    get_weather,
    save_soil_reading,
    get_latest_soil,
    get_soil_history,
    get_weather_history,
    now_ist,
)
from mongo_query import fetch_current_weather, fetch_forecast
from recommendation import generate_recommendation, get_crop_stage
from notifications import create_notification
import json
from datetime import datetime, timedelta, time

farmer_bp = Blueprint('farmer', __name__)

def farmer_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'farmer':
            flash('Access denied', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated

def _parse_farm_id(value):
    try:
        return int(value) if value not in (None, '') else None
    except (TypeError, ValueError):
        return None

def _get_farmer_farms(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT f.*, c.name AS crop_name, c.moisture_threshold,
               c.growth_duration, c.water_requirement, c.stages AS crop_stages,
               z.name AS zone_name
        FROM farms f
        LEFT JOIN crops c ON f.crop_id = c.id
        LEFT JOIN agro_zones z ON f.zone_id = z.id
        WHERE f.user_id = %s
        ORDER BY f.id DESC
        """,
        (user_id,),
    )
    farms = cursor.fetchall()
    conn.close()
    return farms

def _get_active_farm(user_id, requested_farm_id=None):
    farms = _get_farmer_farms(user_id)
    if not farms:
        session.pop('active_farm_id', None)
        return farms, None

    farms_by_id = {farm['id']: farm for farm in farms}
    candidate = requested_farm_id or _parse_farm_id(session.get('active_farm_id'))
    active_farm = farms_by_id.get(candidate) if candidate else None

    if not active_farm:
        active_farm = farms[0]

    session['active_farm_id'] = active_farm['id']
    return farms, active_farm

def _get_crop(crop_id):
    if not crop_id:
        return None
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM crops WHERE id = %s", (crop_id,))
    crop = cursor.fetchone()
    conn.close()
    return crop

def _refresh_weather(farm):
    if not farm:
        return None

    location = (farm.get("location") or "").strip()
    if not location:
        return get_weather(farm["id"])

    live = fetch_current_weather(location)
    if live:
        save_weather(farm["id"], location, live)

    return get_weather(farm["id"])

def _build_farm_view(farm):
    if not farm:
        return {
            'rec': None,
            'weather_doc': None,
            'soil_reading': None,
            'forecast': [],
            'crop': None,
        }

    weather_doc = _refresh_weather(farm)
    soil_reading = get_latest_soil(farm['id'])
    forecast = fetch_forecast(farm.get("location", ""), days=3)
    crop = _get_crop(farm.get("crop_id"))
    rec = generate_recommendation(farm, crop, soil_reading, weather_doc, forecast)

    return {
        'rec': rec,
        'weather_doc': weather_doc,
        'soil_reading': soil_reading,
        'forecast': forecast,
        'crop': crop,
    }

def _combine_schedule_datetime(schedule_row):
    scheduled_date = schedule_row.get('scheduled_date')
    scheduled_time = schedule_row.get('scheduled_time') or time(hour=0, minute=0)
    if not scheduled_date:
        return None
    if isinstance(scheduled_time, timedelta):
        total_seconds = int(scheduled_time.total_seconds())
        scheduled_time = time(
            hour=(total_seconds // 3600) % 24,
            minute=(total_seconds % 3600) // 60, 
            second=total_seconds % 60
        )
    return datetime.combine(scheduled_date, scheduled_time)

def _derive_schedule_status(schedule_row, current_time):
    start_at = _combine_schedule_datetime(schedule_row)
    duration_minutes = int(schedule_row.get('duration_minutes') or 0)
    if not start_at:
        return 'pending'

    end_at = start_at + timedelta(minutes=duration_minutes)
    if current_time < start_at:
        return 'pending'
    if start_at <= current_time < end_at:
        return 'progressing'
    return 'done'

def _sync_irrigation_statuses(farm_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT * FROM irrigation_schedules
        WHERE farm_id = %s
        ORDER BY scheduled_date DESC, scheduled_time DESC, id DESC
        """,
        (farm_id,),
    )
    schedules = cursor.fetchall()
    now_local = now_ist()

    changed = False
    for schedule_row in schedules:
        derived_status = _derive_schedule_status(schedule_row, now_local)
        if schedule_row.get('status') != derived_status:
            cursor.execute(
                "UPDATE irrigation_schedules SET status = %s WHERE id = %s",
                (derived_status, schedule_row['id']),
            )
            schedule_row['status'] = derived_status
            changed = True

    if changed:
        conn.commit()
    conn.close()
    return schedules

@farmer_bp.route('/dashboard')
@farmer_required
def dashboard():
    requested_farm_id = _parse_farm_id(request.args.get('farm_id'))
    farms, farm = _get_active_farm(session['user_id'], requested_farm_id)

    rec = None
    weather_doc = None
    soil_reading = None
    forecast = []
    alerts_db = []
    irrigation_schedules = []
    moisture_chart_data = []
    advisories = []
    weather_history = []

    if farm:
        farm_id = farm['id']
        farm_view = _build_farm_view(farm)
        rec = farm_view['rec']
        weather_doc = farm_view['weather_doc']
        soil_reading = farm_view['soil_reading']
        forecast = farm_view['forecast']

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        if rec and rec["alerts"]:
            for alert in rec["alerts"]:
                cursor.execute(
                    """
                    INSERT INTO alerts (farm_id, alert_type, message, severity)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (farm_id, alert["type"], alert["message"], alert["type"]),
                )

                if alert["type"] in ('critical', 'warning'):
                    conn3 = get_db()
                    cur3 = conn3.cursor(dictionary=True)
                    two_hours_ago = (now_ist() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
                    cur3.execute(
                        """
                        SELECT id FROM notifications
                        WHERE user_id = %s AND message = %s AND created_at > %s
                        LIMIT 1
                        """,
                        (session['user_id'], alert["message"], two_hours_ago),
                    )
                    already_exists = cur3.fetchone()
                    conn3.close()

                    if not already_exists:
                        create_notification(
                            user_id=session['user_id'],
                            title=f'Farm Alert: {alert["type"].title()}',
                            message=alert["message"],
                            ntype=alert["type"],
                            link=f'/farmer/recommendation?farm_id={farm_id}',
                        )
            conn.commit()

        if rec and rec['priority'] in ('critical', 'warning'):
            conn2 = get_db()
            cur2 = conn2.cursor(dictionary=True)
            two_hours_ago = (now_ist() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
            cur2.execute(
                """
                SELECT id FROM notifications
                WHERE user_id = %s AND title = %s AND created_at > %s
                LIMIT 1
                """,
                (session['user_id'], f'{rec["icon"]} AI Recommendation: {rec["action"]}', two_hours_ago),
            )
            already_sent = cur2.fetchone()
            conn2.close()
            if not already_sent:
                create_notification(
                    user_id=session['user_id'],
                    title=f'{rec["icon"]} AI Recommendation: {rec["action"]}',
                    message=rec["reason"],
                    ntype=rec['priority'],
                    link=f'/farmer/recommendation?farm_id={farm_id}',
                )

        cursor.execute(
            "SELECT * FROM alerts WHERE farm_id = %s ORDER BY created_at DESC LIMIT 6",
            (farm_id,),
        )
        alerts_db = cursor.fetchall()

        irrigation_schedules = _sync_irrigation_statuses(farm_id)[:5]

        cursor.execute(
            """
            SELECT a.*, u.name AS operator_name
            FROM advisories a JOIN users u ON a.operator_id = u.id
            WHERE a.is_published = 1
            ORDER BY a.created_at DESC
            LIMIT 3
            """
        )
        advisories = cursor.fetchall()
        conn.close()

        soil_hist = get_soil_history(farm_id, days=14)
        for reading in reversed(soil_hist):
            moisture_chart_data.append({
                "date": reading["recorded_at"].strftime("%b %d"),
                "moisture": round(reading["soil_moisture"], 1),
                "temp": weather_doc["temp"] if weather_doc else 0,
                "rain": weather_doc["rainfall_mm"] if weather_doc else 0,
            })

        weather_history = get_weather_history(farm_id, days=4)

    return render_template(
        'farmer/dashboard.html',
        farms=farms,
        active_farm=farm,
        active_farm_id=farm['id'] if farm else None,
        farm=farm,
        rec=rec,
        weather=weather_doc,
        soil_reading=soil_reading,
        forecast=forecast,
        alerts=alerts_db,
        irrigation_schedules=irrigation_schedules,
        advisories=advisories,
        moisture_data=json.dumps(moisture_chart_data),
        weather_history=weather_history,
    )

@farmer_bp.route('/log-soil', methods=['POST'])
@farmer_required
def log_soil():
    requested_farm_id = _parse_farm_id(request.form.get('farm_id'))
    _, farm = _get_active_farm(session['user_id'], requested_farm_id)
    if not farm:
        flash('Create a farm profile first.', 'error')
        return redirect(url_for('farmer.dashboard'))

    try:
        moisture = float(request.form.get('soil_moisture', 0))
        if not (0 <= moisture <= 100):
            raise ValueError
    except ValueError:
        flash('Invalid moisture value. Enter a number between 0 and 100.', 'error')
        return redirect(url_for('farmer.dashboard', farm_id=farm['id']))

    save_soil_reading(farm['id'], session['user_id'], moisture)
    log_action(session['user_id'], 'log_soil', f'Soil moisture logged for farm "{farm["name"]}": {moisture}%')
    flash(f'Soil moisture {moisture}% logged successfully for {farm["name"]}!', 'success')

    next_url = request.form.get('next') or url_for('farmer.dashboard', farm_id=farm['id'])
    return redirect(next_url)

@farmer_bp.route('/recommendation')
@farmer_required
def recommendation():
    requested_farm_id = _parse_farm_id(request.args.get('farm_id'))
    farms, farm = _get_active_farm(session['user_id'], requested_farm_id)
    if not farm:
        flash('Set up your farm profile first.', 'info')
        return redirect(url_for('farmer.profile'))

    farm_view = _build_farm_view(farm)
    crop = farm_view['crop']
    stage = get_crop_stage(farm.get("planting_date"), crop.get("growth_duration") if crop else 120)
    soil_history = get_soil_history(farm['id'], days=7)

    return render_template(
        'farmer/recommendation.html',
        farms=farms,
        active_farm=farm,
        active_farm_id=farm['id'],
        farm=farm,
        crop=crop,
        rec=farm_view['rec'],
        stage=stage,
        weather=farm_view['weather_doc'],
        soil_reading=farm_view['soil_reading'],
        forecast=farm_view['forecast'],
        soil_history=soil_history,
    )

@farmer_bp.route('/profile', methods=['GET', 'POST'])
@farmer_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        if action == 'update_user':
            cursor.execute(
                "UPDATE users SET name = %s, phone = %s WHERE id = %s",
                (request.form.get('name'), request.form.get('phone'), session['user_id']),
            )
            conn.commit()
            conn.close()
            session['user_name'] = request.form.get('name')
            flash('Profile updated!', 'success')
            return redirect(url_for('farmer.profile'))

        if action == 'set_active_farm':
            conn.close()
            farm_id = _parse_farm_id(request.form.get('farm_id'))
            _, farm = _get_active_farm(session['user_id'], farm_id)
            if farm:
                flash(f'{farm["name"]} is now your active farm.', 'success')
                return redirect(url_for('farmer.profile', farm_id=farm['id']))
            flash('Farm not found.', 'error')
            return redirect(url_for('farmer.profile'))

        if action == 'create_farm':
            cursor.execute(
                """
                INSERT INTO farms (user_id, name, location, area, crop_id, zone_id,
                                   soil_type, irrigation_type, planting_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session['user_id'],
                    request.form.get('farm_name'),
                    request.form.get('location'),
                    request.form.get('area'),
                    request.form.get('crop_id') or None,
                    request.form.get('zone_id') or None,
                    request.form.get('soil_type'),
                    request.form.get('irrigation_type'),
                    request.form.get('planting_date') or None,
                ),
            )
            conn.commit()
            new_farm_id = cursor.lastrowid
            conn.close()

            session['active_farm_id'] = new_farm_id
            log_action(session['user_id'], 'create_farm', f'Farm created: {request.form.get("farm_name")}')

            try:
                conn_op = get_db()
                cur_op = conn_op.cursor(dictionary=True)
                cur_op.execute("SELECT id FROM users WHERE role = 'operator'")
                operators = cur_op.fetchall()
                zone_id_val = request.form.get('zone_id')
                zone_name_val = '—'
                if zone_id_val:
                    cur_op.execute("SELECT name FROM agro_zones WHERE id = %s", (zone_id_val,))
                    zone_row = cur_op.fetchone()
                    if zone_row:
                        zone_name_val = zone_row['name']
                conn_op.close()

                for operator in operators:
                    create_notification(
                        user_id=operator['id'],
                        title=f'New Farm Created by {session["user_name"]}',
                        message=(
                            f'Farmer {session["user_name"]} created farm '
                            f'"{request.form.get("farm_name")}" in zone "{zone_name_val}".'
                        ),
                        ntype='info',
                        link='/operator/farmers',
                    )
            except Exception:
                pass

            flash('Farm created!', 'success')
            return redirect(url_for('farmer.profile', farm_id=new_farm_id))

        if action == 'update_farm':
            farm_id = _parse_farm_id(request.form.get('farm_id'))
            cursor.execute(
                """
                UPDATE farms
                SET name = %s, location = %s, area = %s, crop_id = %s,
                    zone_id = %s, soil_type = %s, irrigation_type = %s, planting_date = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    request.form.get('farm_name'),
                    request.form.get('location'),
                    request.form.get('area'),
                    request.form.get('crop_id') or None,
                    request.form.get('zone_id') or None,
                    request.form.get('soil_type'),
                    request.form.get('irrigation_type'),
                    request.form.get('planting_date') or None,
                    farm_id,
                    session['user_id'],
                ),
            )
            conn.commit()
            conn.close()
            session['active_farm_id'] = farm_id
            flash('Farm updated!', 'success')
            return redirect(url_for('farmer.profile', farm_id=farm_id))

        conn.close()

    requested_farm_id = _parse_farm_id(request.args.get('farm_id'))
    farms, active_farm = _get_active_farm(session['user_id'], requested_farm_id)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM crops ORDER BY name")
    crops = cursor.fetchall()
    cursor.execute("SELECT * FROM agro_zones ORDER BY name")
    zones = cursor.fetchall()
    conn.close()

    editing_farm = None
    if not request.args.get('new_farm'):
        editing_farm_id = _parse_farm_id(request.args.get('edit_farm_id')) or (active_farm['id'] if active_farm else None)
        editing_farm = next((farm for farm in farms if farm['id'] == editing_farm_id), None)

    return render_template(
        'farmer/profile.html',
        user=user,
        farms=farms,
        active_farm=active_farm,
        active_farm_id=active_farm['id'] if active_farm else None,
        farm=editing_farm,
        crops=crops,
        zones=zones,
        today_date=datetime.now().strftime('%Y-%m-%d'),
    )

@farmer_bp.route('/schedule', methods=['GET', 'POST'])
@farmer_required
def schedule():
    requested_farm_id = _parse_farm_id(request.values.get('farm_id'))
    farms, farm = _get_active_farm(session['user_id'], requested_farm_id)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST' and farm and request.form.get('action') == 'add_schedule':
        cursor.execute(
            """
            INSERT INTO irrigation_schedules
            (farm_id, scheduled_date, scheduled_time, duration_minutes, water_amount, reason, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                farm['id'],
                request.form.get('scheduled_date'),
                request.form.get('scheduled_time') or '00:00:00',
                request.form.get('duration_minutes', 45),
                request.form.get('water_amount', 400),
                request.form.get('reason', ''),
                'pending',
            ),
        )
        conn.commit()
        conn.close()

        log_action(session['user_id'], 'add_schedule', f'Irrigation scheduled for farm "{farm["name"]}"')
        create_notification(
            user_id=session['user_id'],
            title='Irrigation Scheduled',
            message=(
                f'Irrigation scheduled for {farm["name"]} on {request.form.get("scheduled_date")} '
                f'at {request.form.get("scheduled_time")} — '
                f'{request.form.get("duration_minutes", 45)} min, {request.form.get("water_amount", 400)} L.'
            ),
            ntype='info',
            link=f'/farmer/schedule?farm_id={farm["id"]}',
        )
        flash('Irrigation scheduled!', 'success')
        return redirect(url_for('farmer.schedule', farm_id=farm['id']))

    schedules = []
    recommendation = None
    weather_doc = None
    soil_reading = None
    crop_threshold = 35

    if farm:
        schedules = _sync_irrigation_statuses(farm['id'])

        farm_view = _build_farm_view(farm)
        recommendation = farm_view['rec']
        weather_doc = farm_view['weather_doc']
        soil_reading = farm_view['soil_reading']

        if farm.get('crop_id'):
            cursor.execute("SELECT moisture_threshold FROM crops WHERE id = %s", (farm['crop_id'],))
            crop_row = cursor.fetchone()
            if crop_row and crop_row['moisture_threshold']:
                crop_threshold = crop_row['moisture_threshold']

    conn.close()

    return render_template(
        'farmer/schedule.html',
        farms=farms,
        active_farm=farm,
        active_farm_id=farm['id'] if farm else None,
        farm=farm,
        farm_today=now_ist().date(),
        schedules=schedules,
        recommendation=recommendation,
        weather=weather_doc,
        soil_reading=soil_reading,
        crop_threshold=crop_threshold,
    )

@farmer_bp.route('/advisories')
@farmer_required
def advisories():
    requested_farm_id = _parse_farm_id(request.args.get('farm_id'))
    farms, farm = _get_active_farm(session['user_id'], requested_farm_id)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT a.*, u.name AS operator_name, c.name AS crop_name, z.name AS zone_name
        FROM advisories a JOIN users u ON a.operator_id = u.id
        LEFT JOIN crops c ON a.crop_id = c.id
        LEFT JOIN agro_zones z ON a.zone_id = z.id
        WHERE a.is_published = 1
        ORDER BY a.created_at DESC
        """
    )
    advisories_list = cursor.fetchall()
    conn.close()

    return render_template(
        'farmer/advisories.html',
        advisories=advisories_list,
        farms=farms,
        active_farm=farm,
        active_farm_id=farm['id'] if farm else None,
        farm=farm,
    )

@farmer_bp.route('/api/sensor/<int:farm_id>')
@farmer_required
def api_sensor(farm_id):
    return jsonify(get_weather(farm_id) or {})

@farmer_bp.route('/api/refresh-weather', methods=['POST'])
@farmer_required
def api_refresh_weather():
    requested_farm_id = _parse_farm_id(request.form.get('farm_id'))
    _, farm = _get_active_farm(session['user_id'], requested_farm_id)
    if not farm:
        return jsonify({"error": "No farm"}), 400

    weather_doc = _refresh_weather(farm)
    if weather_doc:
        weather_doc.pop('_id', None)
        if 'fetched_at' in weather_doc and weather_doc['fetched_at']:
            weather_doc['fetched_at'] = weather_doc['fetched_at'].isoformat()
    return jsonify(weather_doc or {})

@farmer_bp.route('/crop-catalog')
@farmer_required
def crop_catalog():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM crops ORDER BY name")
    crops = cursor.fetchall()
    cursor.execute("SELECT * FROM agro_zones ORDER BY name")
    zones = cursor.fetchall()

    crop_zone_map = {
        'sugarcane': ['tropical', 'alluvial', 'monsoon'],
        'rice': ['deltaic', 'humid', 'lowland', 'flood'],
        'soybean': ['semi-arid', 'black', 'vertisol', 'rainfed'],
        'wheat': ['alluvial', 'subtropical', 'loam'],
        'cotton': ['black', 'semi-arid', 'vertisol'],
        'maize': ['tropical', 'loam', 'alluvial'],
    }

    for crop in crops:
        crop_name_lower = crop['name'].lower()
        keywords = []
        for key, keyword_list in crop_zone_map.items():
            if key in crop_name_lower:
                keywords = keyword_list
                break

        suggested = []
        for zone in zones:
            zone_text = f"{zone['climate']} {zone['soil_type']} {zone['description']}".lower()
            if any(keyword in zone_text for keyword in keywords):
                suggested.append(zone['name'])

        crop['suggested_zones'] = suggested if suggested else ['Suitable for most zones — consult your advisor']
        crop['stages_list'] = [stage.strip() for stage in (crop.get('stages') or '').split(';') if stage.strip()]

    conn.close()
    return render_template('farmer/crop_catalog.html', crops=crops, zones=zones)