from datetime import datetime

from app import mongo_db

from bson import ObjectId



# ------------------------------------------------------------------ #

# Sensor Readings  (time-series → MongoDB)

# ------------------------------------------------------------------ #

class SensorReading:

    COLLECTION = 'sensor_readings'

    @staticmethod

    def insert(sensor_uid, zone_id, sensor_type, value, unit, recorded_at=None):

        doc = {

            'sensor_uid':  sensor_uid,

            'zone_id':     zone_id,

            'sensor_type': sensor_type,   # soil_moisture / weather / rain

            'value':       value,

            'unit':        unit,

            'recorded_at': recorded_at or datetime.utcnow(),

            'created_at':  datetime.utcnow(),

        }

        result = mongo_db[SensorReading.COLLECTION].insert_one(doc)

        return str(result.inserted_id)

    @staticmethod

    def get_latest_by_zone(zone_id, sensor_type=None, limit=50):

        query = {'zone_id': zone_id}

        if sensor_type:

            query['sensor_type'] = sensor_type

        cursor = (

            mongo_db[SensorReading.COLLECTION]

            .find(query)

            .sort('recorded_at', -1)

            .limit(limit)

        )

        return list(cursor)

    @staticmethod

    def get_trend(zone_id, sensor_type, period='daily'):

        """Return aggregated readings grouped by day/week/month."""

        pipeline = [

            {'$match': {'zone_id': zone_id, 'sensor_type': sensor_type}},

            {'$sort': {'recorded_at': -1}},

            {'$limit': 200},

            {'$group': {

                '_id': {

                    'year':  {'$year': '$recorded_at'},

                    'month': {'$month': '$recorded_at'},

                    'day':   {'$dayOfMonth': '$recorded_at'},

                },

                'avg_value': {'$avg': '$value'},

                'max_value': {'$max': '$value'},

                'min_value': {'$min': '$value'},

                'count':     {'$sum': 1},

            }},

            {'$sort': {'_id': 1}},

        ]

        return list(mongo_db[SensorReading.COLLECTION].aggregate(pipeline))

    @staticmethod

    def bulk_insert(readings: list):

        if readings:

            mongo_db[SensorReading.COLLECTION].insert_many(readings)



# ------------------------------------------------------------------ #

# Advisories (created by operator, fetched by farmers)

# ------------------------------------------------------------------ #

class Advisory:

    COLLECTION = 'advisories'

    @staticmethod

    def create(zone_id, crop_stage, advisory_type, title, content, created_by):

        doc = {

            'zone_id':       zone_id,

            'crop_stage':    crop_stage,

            'advisory_type': advisory_type,  # irrigation / nutrient / pest

            'title':         title,

            'content':       content,

            'created_by':    created_by,

            'published':     True,

            'created_at':    datetime.utcnow(),

        }

        result = mongo_db[Advisory.COLLECTION].insert_one(doc)

        return str(result.inserted_id)

    @staticmethod

    def get_by_zone(zone_id, limit=20):

        cursor = (

            mongo_db[Advisory.COLLECTION]

            .find({'zone_id': zone_id, 'published': True})

            .sort('created_at', -1)

            .limit(limit)

        )

        return list(cursor)

    @staticmethod

    def get_all_for_operator(created_by, limit=50):

        cursor = (

            mongo_db[Advisory.COLLECTION]

            .find({'created_by': created_by})

            .sort('created_at', -1)

            .limit(limit)

        )

        return list(cursor)

    @staticmethod

    def delete(advisory_id):

        mongo_db[Advisory.COLLECTION].delete_one({'_id': ObjectId(advisory_id)})



# ------------------------------------------------------------------ #

# Notifications / Alerts

# ------------------------------------------------------------------ #

class Notification:

    COLLECTION = 'notifications'

    @staticmethod

    def create(user_id, zone_id, notif_type, message):

        """

        notif_type: threshold_alert | rain_avoid | stage_change | schedule_reminder

        """

        doc = {

            'user_id':    user_id,

            'zone_id':    zone_id,

            'notif_type': notif_type,

            'message':    message,

            'is_read':    False,

            'created_at': datetime.utcnow(),

        }

        mongo_db[Notification.COLLECTION].insert_one(doc)

    @staticmethod

    def get_unread(user_id, limit=30):

        cursor = (

            mongo_db[Notification.COLLECTION]

            .find({'user_id': user_id, 'is_read': False})

            .sort('created_at', -1)

            .limit(limit)

        )

        return list(cursor)

    @staticmethod

    def get_all(user_id, limit=50):

        cursor = (

            mongo_db[Notification.COLLECTION]

            .find({'user_id': user_id})

            .sort('created_at', -1)

            .limit(limit)

        )

        return list(cursor)

    @staticmethod

    def mark_read(notif_id):

        mongo_db[Notification.COLLECTION].update_one(

            {'_id': ObjectId(notif_id)},

            {'$set': {'is_read': True}}

        )

    @staticmethod

    def mark_all_read(user_id):

        mongo_db[Notification.COLLECTION].update_many(

            {'user_id': user_id},

            {'$set': {'is_read': True}}

        )

    @staticmethod

    def unread_count(user_id):

        return mongo_db[Notification.COLLECTION].count_documents(

            {'user_id': user_id, 'is_read': False}

        )



# ------------------------------------------------------------------ #

# Weather Overlay Cache

# ------------------------------------------------------------------ #

class WeatherCache:

    COLLECTION = 'weather_cache'

    @staticmethod

    def upsert(lat, lon, data: dict):

        mongo_db[WeatherCache.COLLECTION].update_one(

            {'lat': lat, 'lon': lon},

            {'$set': {**data, 'updated_at': datetime.utcnow()}},

            upsert=True

        )

    @staticmethod

    def get(lat, lon):

        return mongo_db[WeatherCache.COLLECTION].find_one({'lat': lat, 'lon': lon})