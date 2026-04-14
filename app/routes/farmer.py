from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from flask_login import login_required, current_user

from functools import wraps

from app.models.farm import FarmProfile, AgroZone, IrrigationSchedule, CropCatalog

from app.models.mongo_models import SensorReading, Advisory, Notification

from datetime import datetime

farmer_bp = Blueprint('farmer', __name__)



def farmer_required(f):

    @wraps(f)

    def decorated(*args, **kwargs):

        if not current_user.is_authenticated or not current_user.is_farmer:

            flash('Access denied.', 'error')

            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated



# ------------------------------------------------------------------ #

# Dashboard

# ------------------------------------------------------------------ #

@farmer_bp.route('/dashboard')

@login_required

@farmer_required

def dashboard():

    farms  = FarmProfile.get_by_user(current_user.id)

    notifs = Notification.get_unread(current_user.id, limit=5)

    notif_count = Notification.unread_count(current_user.id)

    # Gather recent schedules across all farms

    schedules = IrrigationSchedule.get_by_farm_user(current_user.id)[:5]

    # Latest sensor data for first zone found

    latest_sensor = None

    if farms:

        zones = AgroZone.get_by_farm(farms[0]['id'])

        if zones:

            readings = SensorReading.get_latest_by_zone(zones[0]['id'], limit=1)

            latest_sensor = readings[0] if readings else None

    return render_template(

        'farmer/dashboard.html',

        farms=farms,

        schedules=schedules,

        notifications=notifs,

        notif_count=notif_count,

        latest_sensor=latest_sensor,

        now_hour=datetime.now().hour   # ✅ FIX ADDED

    )



# ------------------------------------------------------------------ #

# Farm Profile

# ------------------------------------------------------------------ #

@farmer_bp.route('/farms')

@login_required

@farmer_required

def farms():

    all_farms = FarmProfile.get_by_user(current_user.id)

    return render_template('farmer/farms.html', farms=all_farms)



@farmer_bp.route('/farms/add', methods=['GET', 'POST'])

@login_required

@farmer_required

def add_farm():

    if request.method == 'POST':

        farm_name = request.form.get('farm_name', '').strip()

        address   = request.form.get('address', '').strip()

        lat       = request.form.get('latitude') or None

        lon       = request.form.get('longitude') or None

        pincode   = request.form.get('pincode', '').strip()

        area      = request.form.get('total_area') or None

        if not farm_name:

            flash('Farm name is required.', 'error')

            return render_template('farmer/farm_form.html', form=request.form, action='add')

        FarmProfile.create(current_user.id, farm_name, address, lat, lon, pincode, area)

        flash('Farm added successfully!', 'success')

        return redirect(url_for('farmer.farms'))

    return render_template('farmer/farm_form.html', form={}, action='add')



@farmer_bp.route('/farms/<int:farm_id>/edit', methods=['GET', 'POST'])

@login_required

@farmer_required

def edit_farm(farm_id):

    farm = FarmProfile.get_by_id(farm_id)

    if not farm or farm['user_id'] != current_user.id:

        flash('Farm not found.', 'error')

        return redirect(url_for('farmer.farms'))

    if request.method == 'POST':

        FarmProfile.update(

            farm_id,

            request.form.get('farm_name', '').strip(),

            request.form.get('address', '').strip(),

            request.form.get('latitude') or None,

            request.form.get('longitude') or None,

            request.form.get('pincode', '').strip(),

            request.form.get('total_area') or None,

        )

        flash('Farm updated.', 'success')

        return redirect(url_for('farmer.farms'))

    return render_template('farmer/farm_form.html', form=farm, action='edit')



@farmer_bp.route('/farms/<int:farm_id>/delete', methods=['POST'])

@login_required

@farmer_required

def delete_farm(farm_id):

    farm = FarmProfile.get_by_id(farm_id)

    if farm and farm['user_id'] == current_user.id:

        FarmProfile.delete(farm_id)

        flash('Farm deleted.', 'info')

    return redirect(url_for('farmer.farms'))



# ------------------------------------------------------------------ #

# Agro-Zones

# ------------------------------------------------------------------ #

@farmer_bp.route('/farms/<int:farm_id>/zones')

@login_required

@farmer_required

def zones(farm_id):

    farm = FarmProfile.get_by_id(farm_id)

    if not farm or farm['user_id'] != current_user.id:

        flash('Farm not found.', 'error')

        return redirect(url_for('farmer.farms'))

    all_zones = AgroZone.get_by_farm(farm_id)

    crops     = CropCatalog.get_all()

    return render_template('farmer/zones.html', farm=farm, zones=all_zones, crops=crops)



@farmer_bp.route('/farms/<int:farm_id>/zones/add', methods=['POST'])

@login_required

@farmer_required

def add_zone(farm_id):

    zone_name = request.form.get('zone_name', '').strip()

    area      = request.form.get('area') or None

    soil_type = request.form.get('soil_type', '').strip()

    if zone_name:

        AgroZone.create(farm_id, zone_name, area, soil_type)

        flash('Zone added.', 'success')

    return redirect(url_for('farmer.zones', farm_id=farm_id))



@farmer_bp.route('/zones/<int:zone_id>/delete', methods=['POST'])

@login_required

@farmer_required

def delete_zone(zone_id):

    zone = AgroZone.get_by_id(zone_id)

    if zone:

        farm = FarmProfile.get_by_id(zone['farm_id'])

        farm_id = zone['farm_id']

        if farm and farm['user_id'] == current_user.id:

            AgroZone.delete(zone_id)

            flash('Zone deleted.', 'info')

        return redirect(url_for('farmer.zones', farm_id=farm_id))

    return redirect(url_for('farmer.farms'))



# ------------------------------------------------------------------ #

# Sensor Data & Monitoring

# ------------------------------------------------------------------ #

@farmer_bp.route('/zones/<int:zone_id>/monitoring')

@login_required

@farmer_required

def monitoring(zone_id):

    zone = AgroZone.get_by_id(zone_id)

    if not zone:

        flash('Zone not found.', 'error')

        return redirect(url_for('farmer.farms'))

    readings  = SensorReading.get_latest_by_zone(zone_id, limit=30)

    moisture  = SensorReading.get_latest_by_zone(zone_id, 'soil_moisture', limit=10)

    weather   = SensorReading.get_latest_by_zone(zone_id, 'weather', limit=10)

    trend     = SensorReading.get_trend(zone_id, 'soil_moisture')

    advisories= Advisory.get_by_zone(zone_id)

    return render_template(

        'farmer/monitoring.html',

        zone=zone,

        readings=readings,

        moisture=moisture,

        weather=weather,

        trend=trend,

        advisories=advisories,

    )



@farmer_bp.route('/zones/<int:zone_id>/upload-sensor', methods=['POST'])

@login_required

@farmer_required

def upload_sensor(zone_id):

    """Manual sensor data upload (CSV row or JSON)."""

    sensor_uid  = request.form.get('sensor_uid', '').strip()

    sensor_type = request.form.get('sensor_type', 'soil_moisture')

    value       = float(request.form.get('value', 0))

    unit        = request.form.get('unit', '%')

    SensorReading.insert(sensor_uid, zone_id, sensor_type, value, unit)

    flash('Sensor reading uploaded.', 'success')

    return redirect(url_for('farmer.monitoring', zone_id=zone_id))



# ------------------------------------------------------------------ #

# Irrigation Scheduling

# ------------------------------------------------------------------ #

@farmer_bp.route('/schedules')

@login_required

@farmer_required

def schedules():

    all_schedules = IrrigationSchedule.get_by_farm_user(current_user.id)

    farms = FarmProfile.get_by_user(current_user.id)

    # Build zone list for dropdown

    all_zones = []

    for farm in farms:

        zones = AgroZone.get_by_farm(farm['id'])

        for z in zones:

            z['farm_name'] = farm['farm_name']

            all_zones.append(z)

    return render_template('farmer/schedules.html', schedules=all_schedules, zones=all_zones)



@farmer_bp.route('/schedules/add', methods=['POST'])

@login_required

@farmer_required

def add_schedule():

    zone_id  = int(request.form.get('zone_id'))

    date     = request.form.get('scheduled_date')

    time     = request.form.get('scheduled_time')

    duration = int(request.form.get('duration_mins', 30))

    method   = request.form.get('method', 'drip')

    sid, status = IrrigationSchedule.create(zone_id, date, time, duration, method, current_user.id)

    if status == 'conflict':

        flash('Schedule created but a conflict was detected for this zone/date.', 'warning')

    else:

        flash('Irrigation schedule created.', 'success')

    return redirect(url_for('farmer.schedules'))



@farmer_bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])

@login_required

@farmer_required

def delete_schedule(schedule_id):

    IrrigationSchedule.delete(schedule_id)

    flash('Schedule deleted.', 'info')

    return redirect(url_for('farmer.schedules'))



# ------------------------------------------------------------------ #

# Notifications

# ------------------------------------------------------------------ #

@farmer_bp.route('/notifications')

@login_required

@farmer_required

def notifications():

    all_notifs  = Notification.get_all(current_user.id)

    notif_count = Notification.unread_count(current_user.id)

    Notification.mark_all_read(current_user.id)

    return render_template('farmer/notifications.html', notifications=all_notifs, notif_count=notif_count)



@farmer_bp.route('/notifications/<notif_id>/read', methods=['POST'])

@login_required

@farmer_required

def mark_notification_read(notif_id):

    Notification.mark_read(notif_id)

    return jsonify({'status': 'ok'})