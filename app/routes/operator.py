from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models.farm import CropCatalog, AgroZone, FarmProfile, IrrigationSchedule
from app.models.mongo_models import Advisory, Notification, SensorReading
from app import mysql

operator_bp = Blueprint('operator', __name__)



def operator_required(f):

    @wraps(f)

    def decorated(*args, **kwargs):

        if not current_user.is_authenticated or not current_user.is_operator:

            flash('Operator access required.', 'error')

            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated



def _all_zones():

    cur = mysql.connection.cursor()

    cur.execute(

        """SELECT z.*, fp.farm_name, u.name AS farmer_name

           FROM agro_zones z

           JOIN farm_profiles fp ON z.farm_id = fp.id

           JOIN users u ON fp.user_id = u.id

           ORDER BY u.name, fp.farm_name, z.zone_name"""

    )

    rows = cur.fetchall()

    cur.close()

    return rows



def _all_farmers():

    cur = mysql.connection.cursor()

    cur.execute("SELECT id, name, email, phone, created_at FROM users WHERE role='farmer' AND is_active=1")

    rows = cur.fetchall()

    cur.close()

    return rows



# ------------------------------------------------------------------ #

# Dashboard

# ------------------------------------------------------------------ #

@operator_bp.route('/dashboard')

@login_required

@operator_required

def dashboard():

    zones   = _all_zones()

    farmers = _all_farmers()

    # Aggregate: schedules this week

    cur = mysql.connection.cursor()

    cur.execute(

        """SELECT status, COUNT(*) as cnt

           FROM irrigation_schedules

           WHERE scheduled_date >= CURDATE() - INTERVAL 7 DAY

           GROUP BY status"""

    )

    schedule_stats = cur.fetchall()

    # Recent advisories

    cur.execute(

        "SELECT COUNT(*) as cnt FROM crop_catalog"

    )

    crop_count = cur.fetchone()['cnt']

    cur.close()

    return render_template(

        'operator/dashboard.html',

        zones=zones,

        farmers=farmers,

        schedule_stats=schedule_stats,

        crop_count=crop_count,

    )



# ------------------------------------------------------------------ #

# Crop Catalog Management

# ------------------------------------------------------------------ #

@operator_bp.route('/crops')

@login_required

@operator_required

def crops():

    all_crops = CropCatalog.get_all()

    return render_template('operator/crops.html', crops=all_crops)



@operator_bp.route('/crops/add', methods=['GET', 'POST'])

@login_required

@operator_required

def add_crop():

    if request.method == 'POST':

        crop_name   = request.form.get('crop_name', '').strip()

        crop_type   = request.form.get('crop_type', '').strip()

        season      = request.form.get('season', '').strip()

        water_req   = request.form.get('water_req_mm') or None

        growth_days = request.form.get('growth_days') or None

        if not crop_name:

            flash('Crop name is required.', 'error')

            return render_template('operator/crop_form.html', form=request.form, action='add')

        CropCatalog.create(crop_name, crop_type, season, water_req, growth_days, current_user.id)

        flash('Crop added to catalog.', 'success')

        return redirect(url_for('operator.crops'))

    return render_template('operator/crop_form.html', form={}, action='add')



@operator_bp.route('/crops/<int:crop_id>/edit', methods=['GET', 'POST'])

@login_required

@operator_required

def edit_crop(crop_id):

    crop = CropCatalog.get_by_id(crop_id)

    if not crop:

        flash('Crop not found.', 'error')

        return redirect(url_for('operator.crops'))

    if request.method == 'POST':

        CropCatalog.update(

            crop_id,

            request.form.get('crop_name', '').strip(),

            request.form.get('crop_type', '').strip(),

            request.form.get('season', '').strip(),

            request.form.get('water_req_mm') or None,

            request.form.get('growth_days') or None,

        )

        flash('Crop updated.', 'success')

        return redirect(url_for('operator.crops'))

    return render_template('operator/crop_form.html', form=crop, action='edit')



@operator_bp.route('/crops/<int:crop_id>/delete', methods=['POST'])

@login_required

@operator_required

def delete_crop(crop_id):

    CropCatalog.delete(crop_id)

    flash('Crop deleted from catalog.', 'info')

    return redirect(url_for('operator.crops'))



# ------------------------------------------------------------------ #

# Advisories

# ------------------------------------------------------------------ #

@operator_bp.route('/advisories')

@login_required

@operator_required

def advisories():

    all_advisories = Advisory.get_all_for_operator(current_user.id)

    zones = _all_zones()

    return render_template('operator/advisories.html', advisories=all_advisories, zones=zones)



@operator_bp.route('/advisories/add', methods=['GET', 'POST'])

@login_required

@operator_required

def add_advisory():

    zones = _all_zones()

    if request.method == 'POST':

        zone_id       = int(request.form.get('zone_id'))

        crop_stage    = request.form.get('crop_stage', '').strip()

        advisory_type = request.form.get('advisory_type', 'irrigation')

        title         = request.form.get('title', '').strip()

        content       = request.form.get('content', '').strip()

        if not title or not content:

            flash('Title and content are required.', 'error')

            return render_template('operator/advisory_form.html', zones=zones, form=request.form)

        Advisory.create(zone_id, crop_stage, advisory_type, title, content, current_user.id)

        # Notify subscribed farmers for this zone

        cur = mysql.connection.cursor()

        cur.execute(

            """SELECT s.user_id FROM advisory_subscriptions s

               WHERE s.zone_id=%s AND s.is_active=1""", (zone_id,)

        )

        subs = cur.fetchall()

        cur.close()

        for sub in subs:

            Notification.create(

                sub['user_id'], zone_id, 'advisory',

                f'New advisory published: {title}'

            )

        flash('Advisory published and farmers notified.', 'success')

        return redirect(url_for('operator.advisories'))

    return render_template('operator/advisory_form.html', zones=zones, form={})



@operator_bp.route('/advisories/<advisory_id>/delete', methods=['POST'])

@login_required

@operator_required

def delete_advisory(advisory_id):

    Advisory.delete(advisory_id)

    flash('Advisory deleted.', 'info')

    return redirect(url_for('operator.advisories'))



# ------------------------------------------------------------------ #

# All Zones Overview & Schedule Adherence

# ------------------------------------------------------------------ #

@operator_bp.route('/zones')

@login_required

@operator_required

def zones():

    all_zones = _all_zones()

    return render_template('operator/zones.html', zones=all_zones)



@operator_bp.route('/zone-usage')

@login_required

@operator_required

def zone_usage():

    """Zone-wise water usage & schedule adherence view."""

    cur = mysql.connection.cursor()

    cur.execute(

        """SELECT z.id AS zone_id, z.zone_name, fp.farm_name, u.name AS farmer_name,

                  COUNT(s.id) AS total_schedules,

                  SUM(CASE WHEN s.status='completed' THEN 1 ELSE 0 END) AS completed,

                  SUM(CASE WHEN s.status='skipped'   THEN 1 ELSE 0 END) AS skipped,

                  SUM(CASE WHEN s.status='conflict'  THEN 1 ELSE 0 END) AS conflicts

           FROM agro_zones z

           JOIN farm_profiles fp ON z.farm_id = fp.id

           JOIN users u ON fp.user_id = u.id

           LEFT JOIN irrigation_schedules s ON s.zone_id = z.id

           GROUP BY z.id, z.zone_name, fp.farm_name, u.name

           ORDER BY u.name"""

    )

    zone_stats = cur.fetchall()

    cur.close()

    return render_template('operator/zone_usage.html', zone_stats=zone_stats)



# ------------------------------------------------------------------ #

# Farmer Management

# ------------------------------------------------------------------ #

@operator_bp.route('/farmers')

@login_required

@operator_required

def farmers():

    all_farmers = _all_farmers()

    return render_template('operator/farmers.html', farmers=all_farmers)



# ------------------------------------------------------------------ #

# Threshold Alerts Management

# ------------------------------------------------------------------ #

@operator_bp.route('/thresholds')

@login_required

@operator_required

def thresholds():

    cur = mysql.connection.cursor()

    cur.execute(

        """SELECT at.*, z.zone_name, fp.farm_name

           FROM alert_thresholds at

           JOIN agro_zones z ON at.zone_id = z.id

           JOIN farm_profiles fp ON z.farm_id = fp.id"""

    )

    all_thresholds = cur.fetchall()

    cur.close()

    zones = _all_zones()

    return render_template('operator/thresholds.html', thresholds=all_thresholds, zones=zones)



@operator_bp.route('/thresholds/set', methods=['POST'])

@login_required

@operator_required

def set_threshold():

    zone_id      = int(request.form.get('zone_id'))

    moisture_low = float(request.form.get('moisture_low_pct', 30))

    moisture_high= float(request.form.get('moisture_high_pct', 80))

    rain_avoid   = float(request.form.get('rain_avoid_mm', 5))

    notif_sms    = 1 if request.form.get('notify_sms') else 0

    notif_email  = 1 if request.form.get('notify_email') else 0

    cur = mysql.connection.cursor()

    cur.execute(

        """INSERT INTO alert_thresholds

           (zone_id, moisture_low_pct, moisture_high_pct, rain_avoid_mm, notify_sms, notify_email)

           VALUES (%s,%s,%s,%s,%s,%s)

           ON DUPLICATE KEY UPDATE

           moisture_low_pct=%s, moisture_high_pct=%s, rain_avoid_mm=%s,

           notify_sms=%s, notify_email=%s""",

        (zone_id, moisture_low, moisture_high, rain_avoid, notif_sms, notif_email,

         moisture_low, moisture_high, rain_avoid, notif_sms, notif_email)

    )

    mysql.connection.commit()

    cur.close()

    flash('Threshold settings saved.', 'success')

    return redirect(url_for('operator.thresholds'))