from database import get_db

def get_latest_sensor(farm_id):
   return None

def get_irrigation_recommendation(farm_id):
   sensor = get_latest_sensor(farm_id)

   if not sensor:
       return {
           'action': 'No Data',
           'reason': 'No sensor data available',
           'color': 'gray'
       }

   moisture = sensor.get('soil_moisture', 0)
   rainfall = sensor.get('rainfall', 0)
   condition = sensor.get('weather_condition', '')

   conn = get_db()
   cursor = conn.cursor(dictionary=True)

   cursor.execute("""
       SELECT f.*, cr.moisture_threshold
       FROM farms f
       LEFT JOIN crops cr ON f.crop_id = cr.id
       WHERE f.id = %s
   """, (farm_id,))
   farm = cursor.fetchone()
   conn.close()

   threshold = farm['moisture_threshold'] if farm and farm.get('moisture_threshold') else 35.0

   if rainfall > 10 or condition == 'Rainy':
       return {
           'action': 'Skip Irrigation',
           'reason': f'Rain detected ({rainfall}mm). Sufficient moisture.',
           'color': '#2196F3'
       }
   elif moisture < threshold - 10:
       return {
           'action': 'Irrigate Now',
           'reason': f'Critical moisture level ({moisture:.1f}%). Immediate irrigation required.',
           'color': '#F44336'
       }
   elif moisture < threshold:
       return {
           'action': 'Schedule Irrigation',
           'reason': f'Moisture below threshold ({moisture:.1f}% < {threshold}%). Plan irrigation soon.',
           'color': '#FF9800'
       }
   elif moisture > 75:
       return {
           'action': 'No Irrigation',
           'reason': f'Soil is well-irrigated ({moisture:.1f}%). No action needed.',
           'color': '#4CAF50'
       }
   else:
       return {
           'action': 'Monitor',
           'reason': f'Moisture at acceptable level ({moisture:.1f}%). Continue monitoring.',
           'color': '#4CAF50'
       }

def generate_alerts(farm_id):
   sensor = get_latest_sensor(farm_id)

   if not sensor:
       return []

   alerts = []

   if sensor.get('soil_moisture', 100) < 25:
       alerts.append({
           'type': 'critical',
           'message': f"🚨 Critical: Soil moisture critically low ({sensor['soil_moisture']}%)"
       })

   if sensor.get('rainfall', 0) > 8:
       alerts.append({
           'type': 'info',
           'message': f"🌧️ Rain detected: {sensor['rainfall']}mm. Skip today's irrigation."
       })

   if sensor.get('temperature', 0) > 38:
       alerts.append({
           'type': 'warning',
           'message': f"🌡️ High temperature alert: {sensor['temperature']}°C. Increase irrigation frequency."
       })

   if sensor.get('humidity', 0) > 85:
       alerts.append({
           'type': 'warning',
           'message': f"💧 High humidity ({sensor['humidity']}%). Risk of fungal infection."
       })

   return alerts

def log_action(user_id, action, details, ip='127.0.0.1'):
   conn = get_db()
   cursor = conn.cursor()

   cursor.execute("INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES (%s,%s,%s,%s)", (user_id, action, details, ip))

   conn.commit()
   conn.close()