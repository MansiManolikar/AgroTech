# from app import mysql

# def execute_query(query, params=(), fetchone=False, commit=False):
#     cur = mysql.connection.cursor()
#     cur.execute(query, params)

#     result = None 
#     if fetchone:
#         result = cur.fetchone()
#     elif fetchall:
#         result = cur.fetchall()

#     if commit:
#         mysql.connection.commit()

#     last_id = cur.lastrowid
#     cur.close()

#     return result if result is not None else last_id

# class FarmProfile:
#     @staticmethod
#     def get_by_user(user_id):
#         return execute_query("select * from farm_profiles where user_id=%s", (user_id,), fetchone=True)

#     @staticmethod
#     def get_by_id(farm_id):
#         return execute_query("select * from farm_profiles where id=%s", (farm_id,), fetchone=True)

#     @staticmethod
#     def create(user_id, name, address, lat, lon, pincode, area):
#         return execute_query("insert into farm_profiles(user_id, farm_name, addess, latitude, longitude, pincode, total_area) values(%s, %s, %s, %s, %s, %s, %s)", (user_id, name, address, lat, lon, pincode, area), commit=True)

#     @staticmethod
#     def update(farm_id, ame, address, lat, lon, pincode, area):
#         execute_query("update farm_profiles set farm_name=%s, address=%s, latitude=%s, longitude=%s, pinode=%s, total_area=%s where id=%s", (name, address,lat, lon, pincode, area, farm_id), commit=True)

#     @staticmethod
#     def delete(farm_id):
#         execute_query("delete from farm_profiles where id=%s", (farm_id,), commit=True)

# class AgroZone:
#     @staticmethod
#     def get_by_farm(farm_id):
#         return execute_query("select * from agro_zones where farm_id=%s", (farm_id,), fetchall=True)

#     @staticmethod
#     def get_by_id(zone_id):
#         return execute_query("select * from agro_zones where id=%s", (zone_id,), fetchone=True)

#     @staticmethod
#     def create(farm_id, name, area, soil):
#         return execute_query("insert into agro_zones(farm_id, name, area, soil_type) values(%s, %s, %s, %s)", (farm_id, name, area, soil), commit=True)

#     @staticmethod
#     def update(zone_id, name, area, soil):
#         execute_query("update agro_zones set zone_name=%s, area=%s, soil_type=%s where id=%s", (name, area, soil, zone_id), commit=True)

#     @staticmethod
#     def delete(zone_id):
#         execute_query("delete from agro_zones where id=%s", (zone_id,), commit=True)

# class CropCatalog:
#     @staticmethod
#     def get_all():
#         return execute_query("select * from crop_catalog order by crop_name", fetchall=True)

#     @staticmethod
#     def get_by_id(crop_id):
#         return execute_query("select * from crop_catalog where id=%s", (crop_id,), fetchone=True)

#     @staticmethod
#     def create(name, type_, season, water, days, created_by):
#         return execute_query("insert into crop_catalog(crop_name, crop_type, season, water_req_mm, growth_days, created_by) values(%s, %s, %s, %s, %s, %s)", (name, type_, season, water, days, created_by), commit=True) 

#     @staticmethod
#     def update(crop_id, name, type_, season, water, days):
#         execute_query("update crop_catalog set crop_name=%s, crop_type=%s, season=%s, water_req_mm=%s, growth_days=%s where id=%s", (name, type_, season, water, days, crop_id), commit=True)

#     @staticmethod
#     def delete(crop_id):
#         execute_query("delete from crop_catalog where id=%s", (crop_id,), commit=True)

# class IrrigationSchedule:
#     @staticmethod
#     def get_by_zone(zone_id):
#         return execute_query("select * from irrigation_schedules where zone_id=%s order by schedule_date, schedule_time", (zone_id,), fetchall=True)

#     @staticmethod
#     def get_by_user(user_id):
#         return execute_query("select s.*, z.zone_name, f.farm_name from irrigation_schedules s join agro_zones z on s.zone_id=z.id join farm_profiles f on z.farm_id=f.id where f.user_id=%s order by s.scheduled_date desc", (user_id,), fetchall=True)

#     @staticmethod
#     def create(zone_id, date, time, duration, method, created_by):
#         conflict = execute_query("select id from irrigation_schedules where zone_id=%s and schedule_date=%s and status='pending'", (zone_id, date), fetchone=True)
#         status = 'conflict' if conflict else 'pending'
#         sid = execute_query("insert into irrigation_schedules(zone_id, scheduled_date, scheduled_time, duration_mins, method, status, created_by) values(%s, %s, %s, %s, %s, %s, %s)", (zone_id, date, time, duration, method, status, created_by), commit=True)
#         return sid, status

#     @staticmethod
#     def update_status(schedule_id, status):
#         execute_query("update irrigation_schedules set status=%s where id=%s", (status, schedule_id), commit=True)

#     @staticmethod
#     def delete(schedule_id):
#         execute_query("delete from irrigation_schedules where id=%s", (schedule_id,), commit=True)

from app import mysql

# ------------------------------------------------------------------ #

# Farm Profile

# ------------------------------------------------------------------ #

class FarmProfile:

    @staticmethod

    def get_by_user(user_id):

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM farm_profiles WHERE user_id = %s", (user_id,))

        rows = cur.fetchall()

        cur.close()

        return rows

    @staticmethod

    def get_by_id(farm_id):

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM farm_profiles WHERE id = %s", (farm_id,))

        row = cur.fetchone()

        cur.close()

        return row

    @staticmethod

    def create(user_id, farm_name, address, lat, lon, pincode, area):

        cur = mysql.connection.cursor()

        cur.execute(

            """INSERT INTO farm_profiles

               (user_id, farm_name, address, latitude, longitude, pincode, total_area)

               VALUES (%s,%s,%s,%s,%s,%s,%s)""",

            (user_id, farm_name, address, lat, lon, pincode, area)

        )

        mysql.connection.commit()

        fid = cur.lastrowid

        cur.close()

        return fid

    @staticmethod

    def update(farm_id, farm_name, address, lat, lon, pincode, area):

        cur = mysql.connection.cursor()

        cur.execute(

            """UPDATE farm_profiles SET farm_name=%s, address=%s,

               latitude=%s, longitude=%s, pincode=%s, total_area=%s

               WHERE id=%s""",

            (farm_name, address, lat, lon, pincode, area, farm_id)

        )

        mysql.connection.commit()

        cur.close()

    @staticmethod

    def delete(farm_id):

        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM farm_profiles WHERE id=%s", (farm_id,))

        mysql.connection.commit()

        cur.close()



# ------------------------------------------------------------------ #

# Agro-Zone

# ------------------------------------------------------------------ #

class AgroZone:

    @staticmethod

    def get_by_farm(farm_id):

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM agro_zones WHERE farm_id=%s", (farm_id,))

        rows = cur.fetchall()

        cur.close()

        return rows

    @staticmethod

    def get_by_id(zone_id):

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM agro_zones WHERE id=%s", (zone_id,))

        row = cur.fetchone()

        cur.close()

        return row

    @staticmethod

    def create(farm_id, zone_name, area, soil_type):

        cur = mysql.connection.cursor()

        cur.execute(

            "INSERT INTO agro_zones (farm_id, zone_name, area, soil_type) VALUES (%s,%s,%s,%s)",

            (farm_id, zone_name, area, soil_type)

        )

        mysql.connection.commit()

        zid = cur.lastrowid

        cur.close()

        return zid

    @staticmethod

    def update(zone_id, zone_name, area, soil_type):

        cur = mysql.connection.cursor()

        cur.execute(

            "UPDATE agro_zones SET zone_name=%s, area=%s, soil_type=%s WHERE id=%s",

            (zone_name, area, soil_type, zone_id)

        )

        mysql.connection.commit()

        cur.close()

    @staticmethod

    def delete(zone_id):

        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM agro_zones WHERE id=%s", (zone_id,))

        mysql.connection.commit()

        cur.close()



# ------------------------------------------------------------------ #

# Crop Catalog

# ------------------------------------------------------------------ #

class CropCatalog:

    @staticmethod

    def get_all():

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM crop_catalog ORDER BY crop_name")

        rows = cur.fetchall()

        cur.close()

        return rows

    @staticmethod

    def get_by_id(crop_id):

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM crop_catalog WHERE id=%s", (crop_id,))

        row = cur.fetchone()

        cur.close()

        return row

    @staticmethod

    def create(crop_name, crop_type, season, water_req_mm, growth_days, created_by):

        cur = mysql.connection.cursor()

        cur.execute(

            """INSERT INTO crop_catalog

               (crop_name, crop_type, season, water_req_mm, growth_days, created_by)

               VALUES (%s,%s,%s,%s,%s,%s)""",

            (crop_name, crop_type, season, water_req_mm, growth_days, created_by)

        )

        mysql.connection.commit()

        cid = cur.lastrowid

        cur.close()

        return cid

    @staticmethod

    def update(crop_id, crop_name, crop_type, season, water_req_mm, growth_days):

        cur = mysql.connection.cursor()

        cur.execute(

            """UPDATE crop_catalog SET crop_name=%s, crop_type=%s,

               season=%s, water_req_mm=%s, growth_days=%s WHERE id=%s""",

            (crop_name, crop_type, season, water_req_mm, growth_days, crop_id)

        )

        mysql.connection.commit()

        cur.close()

    @staticmethod

    def delete(crop_id):

        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM crop_catalog WHERE id=%s", (crop_id,))

        mysql.connection.commit()

        cur.close()



# ------------------------------------------------------------------ #

# Irrigation Schedule

# ------------------------------------------------------------------ #

class IrrigationSchedule:

    @staticmethod

    def get_by_zone(zone_id):

        cur = mysql.connection.cursor()

        cur.execute(

            "SELECT * FROM irrigation_schedules WHERE zone_id=%s ORDER BY scheduled_date, scheduled_time",

            (zone_id,)

        )

        rows = cur.fetchall()

        cur.close()

        return rows

    @staticmethod

    def get_by_farm_user(user_id):

        cur = mysql.connection.cursor()

        cur.execute(

            """SELECT s.*, z.zone_name, fp.farm_name

               FROM irrigation_schedules s

               JOIN agro_zones z ON s.zone_id = z.id

               JOIN farm_profiles fp ON z.farm_id = fp.id

               WHERE fp.user_id = %s

               ORDER BY s.scheduled_date DESC""",

            (user_id,)

        )

        rows = cur.fetchall()

        cur.close()

        return rows

    @staticmethod

    def create(zone_id, date, time, duration, method, created_by):

        # Check for conflict on same zone/date

        cur = mysql.connection.cursor()

        cur.execute(

            """SELECT id FROM irrigation_schedules

               WHERE zone_id=%s AND scheduled_date=%s AND status='pending'""",

            (zone_id, date)

        )

        conflict = cur.fetchone()

        status = 'conflict' if conflict else 'pending'

        cur.execute(

            """INSERT INTO irrigation_schedules

               (zone_id, scheduled_date, scheduled_time, duration_mins, method, status, created_by)

               VALUES (%s,%s,%s,%s,%s,%s,%s)""",

            (zone_id, date, time, duration, method, status, created_by)

        )

        mysql.connection.commit()

        sid = cur.lastrowid

        cur.close()

        return sid, status

    @staticmethod

    def update_status(schedule_id, status):

        cur = mysql.connection.cursor()

        cur.execute(

            "UPDATE irrigation_schedules SET status=%s WHERE id=%s",

            (status, schedule_id)

        )

        mysql.connection.commit()

        cur.close()

    @staticmethod

    def delete(schedule_id):

        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM irrigation_schedules WHERE id=%s", (schedule_id,))

        mysql.connection.commit()

        cur.close()