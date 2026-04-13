from app import mysql

def execute_query(query, params=(), fetchone=False, commit=False):
    cur = mysql.connection.cursor()
    cur.execute(query, params)

    result = None 
    if fetchone:
        result = cur.fetchone()
    elif fetchall:
        result = cur.fetchall()

    if commit:
        mysql.connection.commit()

    last_id = cur.lastrowid
    cur.close()

    return result if result is not None els last_id

class FarmProfile:
    @staticmethod
    def get_by_user(user_id):
        return execute_query("select * from farm_profiles where user_id=%s", (user_id,), fetchall=True)

    @staticmethod
    def get_by_id(farm_id):
        return execute_query("select * from farm_profiles where id=%s", (farm_id,), fetchone=True)

    @staticmethod
    def create(user_id, name, address, lat, lon, pincode, area):
        return execute_query("insert into farm_profiles(user_id, farm_name, addess, latitude, longitude, pincode, total_area) values(%s, %s, %s, %s, %s, %s, %s)", (user_id, name, address, lat, lon, pincode, area), commit=True)

    @staticmethod
    def update(farm_id, ame, address, lat, lon, pincode, area):
        execute_query("update farm_profiles set farm_name=%s, address=%s, latitude=%s, longitude=%s, pinode=%s, total_area=%s where id=%s", (name, address,lat, lon, pincode, area, farm_id), commit=True)

    @staticmethod
    def delete(farm_id):
        execute_query("delete from farm_profiles where id=%s", (farm_id,), commit=True)

class ArgoZone:
    @staticmethod
    def get_by_farm(farm_id):
        return execute_query("select * from agro_zones where farm_id=%s", (farm_id,), fetchall=True)

    @staticmethod
    def get_by_id(zone_id):
        return execute_query("select * from agro_zones where id=%s", (zone_id,), fetchone=True)

    @staticmethod
    def create(farm_id, name, area, soil):
        return execute_query("insert into agro_zones(farm_id, name, area, soil_type) values(%s, %s, %s, %s)", (farm_id, name, area, soil), commit=True)

    @staticmethod
    def update(zone_id, name, area, soil):
        execute_query("update agro_zones set zone_name=%s, area=%s, soil_type=%s where id=%s", (name, area, soil, zone_id), commit=True)

    @staticmethod
    def delete(zone_id):
        execute_query("delete from agro_zones where id=%s", (zone_id,), commit=True)

class CropCatalog:
    @staticmethod
    def get_all():
        return execute_query("select * from crop_catalog order by crop_name", fetchall=True)

    @staticmethod
    def get_by_id(crop_id):
        return execute_query("select * from crop_catalog where id=%s", (crop_id,), fetchone=True)

    @staticmethod
    def create(name, type_, season, water, days, created_by):
        return execute_query("insert into crop_catalog(crop_name, crop_type, season, water_req_mm, growth_days, created_by) values(%s, %s, %s, %s, %s, %s)", (name, type_, season, water, days, created_by), commit=True) 

    @staticmethod
    def update(crop_id, name, type_, season, water, days):
        execute_query("update crop_catalog set crop_name=%s, crop_type=%s, season=%s, water_req_mm=%s, growth_days=%s where id=%s", (name, type_, season, water, days, crop_id), commit=True)

    @staticmethod
    def delete(crop_id):
        execute_query("delete from crop_catalog where id=%s", (crop_id,), commit=True)

class IrrigationSchedule:
    @staticmethod
    def get_by_zone(zone_id):
        return execute_query("select * from irrigation_schedules where zone_id=%s order by schedule_date, schedule_time", (zone_id,), fetchall=True)

    @staticmethod
    def get_by_user(user_id):
        return execute_query("select s.*, z.zone_name, f.farm_name from irrigation_schedules s join agro_zones z on s.zone_id=z.id join farm_profiles f on z.farm_id=f.id where f.user_id=%s order by s.scheduled_date desc", (user_id,), fetchall=True)

    @staticmethod
    def create(zone_id, date, time, duration, method, created_by):
        conflict = execute_query("select id from irrigation_schedules where zone_id=%s and schedule_date=%s and status='pending'", (zone_id, date), fetchone=True)
        status = 'conflict' if conflict else 'pending'
        sid = execute_query("insert into irrigation_schedules(zone_id, scheduled_date, scheduled_time, duration_mins, method, status, created_by) values(%s, %s, %s, %s, %s, %s, %s)", (zone_id, date, time, duration, method, status, created_by), commit=True)
        return sid, status

    @staticmethod
    def update_status(schedule_id, status):
        execute_query("update irrigation_schedules set status=%s where id=%s", (status, schedule_id), commit=True)

    @staticmethod
    def delete(schedule_id):
        execute_query("delete from irrigation_schedules where id=%s", (schedule_id,), commit=True)