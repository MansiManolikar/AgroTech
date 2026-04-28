from pymongo import MongoClient, DESCENDING
from datetime import datetime, timedelta
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = "agritech"

IST_OFFSET = timedelta(hours=5, minutes=30)

def utc_to_ist(dt):
    if dt is None:
        return None
    return dt + IST_OFFSET

def now_ist():
    return datetime.utcnow() + IST_OFFSET

def get_mongo():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB]


def save_weather(farm_id: int, location: str, data: dict):
    db = get_mongo()
    snapshot = {
        "farm_id": farm_id,
        "location": location,
        "fetched_at": now_ist(),
        "temp": data.get("temp_c"),
        "feels_like": data.get("feelslike_c"),
        "humidity": data.get("humidity"),
        "wind_kph": data.get("wind_kph"),
        "rainfall_mm": data.get("precip_mm", 0),
        "condition": data.get("condition"),
        "uv_index": data.get("uv"),
    }

    db.farm_weather.update_one(
        {"farm_id": farm_id},
        {"$set": snapshot},
        upsert=True
    )
    db.farm_weather_history.insert_one(snapshot)

def get_weather(farm_id: int):
    db = get_mongo()
    return db.farm_weather.find_one({"farm_id": farm_id})

def save_soil_reading(farm_id: int, user_id: int, moisture: float):
    db = get_mongo()
    db.soil_readings.insert_one({
        "farm_id": farm_id,
        "user_id": user_id,
        "soil_moisture": moisture,
        "recorded_at": now_ist(),
    })

def get_latest_soil(farm_id: int):
    db = get_mongo()
    return db.soil_readings.find_one(
        {"farm_id": farm_id},
        sort=[("recorded_at", DESCENDING)]
    )

def get_soil_history(farm_id: int, days: int = 14):
    db = get_mongo()
    since = now_ist() - timedelta(days=days)
    cursor = db.soil_readings.find(
        {"farm_id": farm_id, "recorded_at": {"$gte": since}},
        sort=[("recorded_at", DESCENDING)]
    ).limit(days)
    return list(cursor)

def get_weather_history(farm_id: int, days: int = 14):
    db = get_mongo()
    since = now_ist() - timedelta(days=days)
    cursor = db.farm_weather_history.find(
        {"farm_id": farm_id, "fetched_at": {"$gte": since}},
        sort=[("fetched_at", DESCENDING)]
    ).limit(days)
    return list(cursor)