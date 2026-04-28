from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db
from helpers import log_action
from notifications import (notify_all_farmers, notify_farmers_by_crop,
                           notify_farmers_by_zone, create_notification, get_unread_count)
from mongo_db import get_weather, get_latest_soil, now_ist
from recommendation import get_crop_stage
import json
from datetime import datetime, timedelta
from collections import defaultdict

operator_bp = Blueprint('operator', __name__)

def operator_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'operator':
            flash('Operator access required', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

def _get_farm_sensor_data(farm_id, crop_moisture_threshold=35, growth_duration=120, planting_date=None):
    weather  = get_weather(farm_id) or {}
    soil     = get_latest_soil(farm_id) or {}
    stage    = get_crop_stage(planting_date, growth_duration)
    return {
        'soil_moisture':     soil.get('soil_moisture'),
        'temp':              weather.get('temp'),
        'weather_condition': weather.get('condition'),
        'rainfall_mm':       weather.get('rainfall_mm', 0),
        'stage_name':        stage.get('name', '—'),
        'stage_index':       stage.get('index', 0),
    }

@operator_bp.route('/dashboard')
@operator_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role='farmer'")
    total_farmers = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM farms")
    total_farms = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM agro_zones")
    total_zones = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM advisories WHERE is_published=1")
    total_advisories = cursor.fetchone()['total']

    cursor.execute("""
        SELECT f.id, f.name, f.location, f.planting_date,
               u.name AS farmer_name,
               c.name AS crop_name, c.moisture_threshold, c.growth_duration
        FROM farms f JOIN users u ON f.user_id = u.id
        LEFT JOIN crops c ON f.crop_id = c.id
    """)
    raw_farms = cursor.fetchall()
    farms_data = []
    for f in raw_farms:
        sensor = _get_farm_sensor_data(
            f['id'],
            f['moisture_threshold'] or 35,
            f['growth_duration'] or 120,
            f['planting_date']
        )
        farms_data.append({**f, **sensor})

    # Real water usage from irrigation_schedules
    cursor.execute("""
        SELECT DATE_FORMAT(scheduled_date,'%b') AS month,
               MONTH(scheduled_date) AS month_num,
               COALESCE(SUM(water_amount),0) AS total_water
        FROM irrigation_schedules
        WHERE YEAR(scheduled_date) = YEAR(CURDATE())
        GROUP BY month, month_num ORDER BY month_num
    """)
    water_rows = cursor.fetchall()
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    water_map = {r['month']: int(r['total_water']) for r in water_rows}
    months_out, water_out = [], []
    for m in month_names[:datetime.now().month]:
        months_out.append(m)
        water_out.append(water_map.get(m, 0))

    cursor.execute("""
        SELECT z.name, COUNT(f.id) AS farm_count FROM agro_zones z
        LEFT JOIN farms f ON f.zone_id = z.id GROUP BY z.id
    """)
    zone_stats = cursor.fetchall()

    # Recent activity log
    cursor.execute("""
        SELECT al.*, u.name AS user_name FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.timestamp DESC LIMIT 10
    """)
    recent_logs = cursor.fetchall()
    conn.close()

    return render_template('operator/dashboard.html',
        total_farmers=total_farmers, total_farms=total_farms,
        total_zones=total_zones, total_advisories=total_advisories,
        farms_data=farms_data,
        months=json.dumps(months_out),
        water_usage=json.dumps(water_out),
        zone_stats=zone_stats,
        recent_logs=recent_logs)

@operator_bp.route('/farmers')
@operator_required
def farmers():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.phone, u.created_at,
               f.id AS farm_id, f.name AS farm_name, f.location, f.area,
               f.planting_date, f.zone_id,
               c.name AS crop_name, c.moisture_threshold, c.growth_duration,
               z.name AS zone_name
        FROM users u
        LEFT JOIN farms f ON f.user_id = u.id
        LEFT JOIN crops c ON f.crop_id = c.id
        LEFT JOIN agro_zones z ON f.zone_id = z.id
        WHERE u.role='farmer'
        ORDER BY u.created_at DESC
    """)
    raw_farmers = cursor.fetchall()

    # Registration timeline
    reg_by_month = defaultdict(int)
    seen_reg_users = set()
    for f in raw_farmers:
        if f['created_at'] and f['id'] not in seen_reg_users:
            key = f['created_at'].strftime('%b %Y')
            reg_by_month[key] += 1
            seen_reg_users.add(f['id'])

    # Attach MongoDB sensor data
    farmers_list = []
    for f in raw_farmers:
        if f['farm_id']:
            sensor = _get_farm_sensor_data(
                f['farm_id'],
                f['moisture_threshold'] or 35,
                f['growth_duration'] or 120,
                f['planting_date']
            )
        else:
            sensor = {'soil_moisture': None, 'temp': None,
                      'weather_condition': None, 'rainfall_mm': 0,
                      'stage_name': '—', 'stage_index': 0}
        farmers_list.append({**f, **sensor})

    conn.close()

    # Build registration chart data from actual DB
    sorted_reg = sorted(reg_by_month.items(), key=lambda item: datetime.strptime(item[0], '%b %Y'))
    reg_labels = [item[0] for item in sorted_reg]
    reg_values = [item[1] for item in sorted_reg]

    # Moisture distribution buckets from real data
    critical = sum(1 for f in farmers_list if f['soil_moisture'] and f['soil_moisture'] < 30)
    monitor  = sum(1 for f in farmers_list if f['soil_moisture'] and 30 <= f['soil_moisture'] < 50)
    good     = sum(1 for f in farmers_list if f['soil_moisture'] and f['soil_moisture'] >= 50)
    no_data  = sum(1 for f in farmers_list if not f['soil_moisture'])

    total_farmers_count = len({f['id'] for f in raw_farmers})

    return render_template('operator/farmers.html',
        farmers=farmers_list,
        total_farmers_count=total_farmers_count,
        moisture_dist=json.dumps([critical, monitor, good, no_data]),
        reg_labels=json.dumps(reg_labels),
        reg_values=json.dumps(reg_values))

@operator_bp.route('/zones', methods=['GET', 'POST'])
@operator_required
def zones():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            name = request.form.get('name')
            cursor.execute(
                "INSERT INTO agro_zones (name, region, soil_type, climate, description) VALUES (%s,%s,%s,%s,%s)",
                (name, request.form.get('region'), request.form.get('soil_type'),
                 request.form.get('climate'), request.form.get('description'))
            )
            conn.commit()
            log_action(session['user_id'], 'create_zone', f'Zone "{name}" created')
            notify_all_farmers(
                title=f'🗺️ New Agro Zone Added: {name}',
                message=f'Admin added a new agricultural zone "{name}". Check the Crop Catalog.',
                ntype='info', link='/farmer/crop-catalog'
            )
            flash('Zone created!', 'success')
        elif action == 'delete':
            zone_id = request.form.get('zone_id')
            cursor.execute("SELECT name FROM agro_zones WHERE id=%s", (zone_id,))
            z = cursor.fetchone()
            cursor.execute("DELETE FROM agro_zones WHERE id=%s", (zone_id,))
            conn.commit()
            if z:
                notify_all_farmers(
                    title=f'🗺️ Agro Zone Removed: {z["name"]}',
                    message=f'The zone "{z["name"]}" has been removed. Please review your farm settings.',
                    ntype='warning'
                )
            flash('Zone deleted!', 'success')

    cursor.execute("""
        SELECT z.*, COUNT(f.id) AS farm_count FROM agro_zones z
        LEFT JOIN farms f ON f.zone_id = z.id GROUP BY z.id
    """)
    zones = cursor.fetchall()
    conn.close()
    return render_template('operator/zones.html', zones=zones)

@operator_bp.route('/crops', methods=['GET', 'POST'])
@operator_required
def crops():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            name = request.form.get('name')
            cursor.execute(
                "INSERT INTO crops (name, variety, growth_duration, water_requirement, moisture_threshold, stages, description) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (name, request.form.get('variety'), request.form.get('growth_duration'),
                 request.form.get('water_requirement'), request.form.get('moisture_threshold'),
                 request.form.get('stages'), request.form.get('description'))
            )
            conn.commit()
            log_action(session['user_id'], 'create_crop', f'Crop "{name}" added to catalog')
            notify_all_farmers(
                title=f'🌱 New Crop Added to Catalog: {name}',
                message=f'Admin added "{name}" to the crop catalog. Visit the Crop Catalog to read details.',
                ntype='success', link='/farmer/crop-catalog'
            )
            flash('Crop added!', 'success')
        elif action == 'delete':
            crop_id = request.form.get('crop_id')
            cursor.execute("SELECT name FROM crops WHERE id=%s", (crop_id,))
            c = cursor.fetchone()
            if c:
                notify_farmers_by_crop(
                    crop_id=int(crop_id),
                    title=f'⚠️ Crop Removed: {c["name"]}',
                    message=f'The crop "{c["name"]}" has been removed. Please update your farm profile.',
                    ntype='warning'
                )
            cursor.execute("DELETE FROM crops WHERE id=%s", (crop_id,))
            conn.commit()
            flash('Crop deleted!', 'success')

    cursor.execute("""
        SELECT c.*, COUNT(f.id) AS farm_count FROM crops c
        LEFT JOIN farms f ON f.crop_id = c.id GROUP BY c.id
    """)
    crops = cursor.fetchall()
    conn.close()
    return render_template('operator/crops.html', crops=crops)

@operator_bp.route('/advisories', methods=['GET', 'POST'])
@operator_required
def advisories():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            title    = request.form.get('title')
            crop_id  = request.form.get('crop_id') or None
            zone_id  = request.form.get('zone_id') or None
            adv_type = request.form.get('advisory_type')
            is_pub   = int(request.form.get('is_published', 1))
            cursor.execute(
                "INSERT INTO advisories (operator_id, title, content, crop_id, zone_id, advisory_type, is_published) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (session['user_id'], title, request.form.get('content'),
                 crop_id, zone_id, adv_type, is_pub)
            )
            conn.commit()
            log_action(session['user_id'], 'create_advisory', f'Advisory "{title}" created')
            if is_pub:
                msg  = f'Admin published a new advisory: "{title}". Check the Advisories section.'
                link = '/farmer/advisories'
                if crop_id:
                    notify_farmers_by_crop(int(crop_id), f'📢 New Advisory: {title}', msg, 'advisory', link)
                elif zone_id:
                    notify_farmers_by_zone(int(zone_id), f'📢 New Advisory: {title}', msg, 'advisory', link)
                else:
                    notify_all_farmers(f'📢 New Advisory: {title}', msg, 'advisory', link)
            flash('Advisory published!', 'success')

        elif action == 'delete':
            cursor.execute("DELETE FROM advisories WHERE id=%s", (request.form.get('advisory_id'),))
            conn.commit()
            flash('Advisory deleted!', 'success')

        elif action == 'toggle':
            adv_id  = request.form.get('advisory_id')
            cursor.execute("SELECT is_published, title, crop_id, zone_id FROM advisories WHERE id=%s", (adv_id,))
            current = cursor.fetchone()
            new_status = 0 if current['is_published'] else 1
            cursor.execute("UPDATE advisories SET is_published=%s WHERE id=%s", (new_status, adv_id))
            conn.commit()
            if new_status == 1 and current:
                title   = current['title']
                crop_id = current['crop_id']
                zone_id = current['zone_id']
                msg     = f'Advisory "{title}" has been published.'
                link    = '/farmer/advisories'
                if crop_id:
                    notify_farmers_by_crop(crop_id, f'📢 Advisory Published: {title}', msg, 'advisory', link)
                elif zone_id:
                    notify_farmers_by_zone(zone_id, f'📢 Advisory Published: {title}', msg, 'advisory', link)
                else:
                    notify_all_farmers(f'📢 Advisory Published: {title}', msg, 'advisory', link)

    cursor.execute("""
        SELECT a.*, u.name AS operator_name, c.name AS crop_name, z.name AS zone_name
        FROM advisories a JOIN users u ON a.operator_id = u.id
        LEFT JOIN crops c ON a.crop_id = c.id
        LEFT JOIN agro_zones z ON a.zone_id = z.id
        ORDER BY a.created_at DESC
    """)
    advisories = cursor.fetchall()
    cursor.execute("SELECT * FROM crops")
    crops = cursor.fetchall()
    cursor.execute("SELECT * FROM agro_zones")
    zones = cursor.fetchall()
    conn.close()
    return render_template('operator/advisories.html', advisories=advisories, crops=crops, zones=zones)

@operator_bp.route('/simulate-data', methods=['POST'])
@operator_required
def simulate_data():
    return jsonify({'status': 'disabled', 'message': 'Sensor data handled by MongoDB'})