from __future__ import annotations

import os

from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = "agritech"
MONGO_COLLECTION = "weather_data"

WEATHER_RECORDS: list[dict] = [

    # ── Kuttanad, Kerala (hot & humid, heavy monsoon) ──────────────────────
    {"state": "Kerala", "district": "Kuttanad", "slot": 0,  # 06-09 ↑
     "weather": {"temp_c": 26.5, "feelslike_c": 30.2, "humidity": 88, "wind_kph": 10.0, "precip_mm": 1.5, "uv": 3.0, "condition": "Patchy rain nearby"}},
    {"state": "Kerala", "district": "Kuttanad", "slot": 1,  # 09-12 ↑
     "weather": {"temp_c": 29.8, "feelslike_c": 34.5, "humidity": 82, "wind_kph": 12.0, "precip_mm": 2.0, "uv": 6.0, "condition": "Partly cloudy"}},
    {"state": "Kerala", "district": "Kuttanad", "slot": 2,  # 12-15 ↑ peak
     "weather": {"temp_c": 32.1, "feelslike_c": 37.8, "humidity": 75, "wind_kph": 14.0, "precip_mm": 0.5, "uv": 9.0, "condition": "Sunny"}},
    {"state": "Kerala", "district": "Kuttanad", "slot": 3,  # 15-18 ↓
     "weather": {"temp_c": 31.0, "feelslike_c": 36.2, "humidity": 78, "wind_kph": 13.0, "precip_mm": 3.5, "uv": 6.0, "condition": "Moderate rain"}},
    {"state": "Kerala", "district": "Kuttanad", "slot": 4,  # 18-21 ↓
     "weather": {"temp_c": 28.5, "feelslike_c": 32.8, "humidity": 84, "wind_kph": 11.0, "precip_mm": 5.0, "uv": 1.0, "condition": "Heavy rain"}},
    {"state": "Kerala", "district": "Kuttanad", "slot": 5,  # 21-00 ↓
     "weather": {"temp_c": 26.8, "feelslike_c": 30.5, "humidity": 89, "wind_kph": 9.0,  "precip_mm": 2.5, "uv": 0.0, "condition": "Patchy rain nearby"}},
    {"state": "Kerala", "district": "Kuttanad", "slot": 6,  # 00-03 ↓ coldest
     "weather": {"temp_c": 25.2, "feelslike_c": 28.8, "humidity": 92, "wind_kph": 8.0,  "precip_mm": 1.0, "uv": 0.0, "condition": "Overcast"}},
    {"state": "Kerala", "district": "Kuttanad", "slot": 7,  # 03-06 ↑
     "weather": {"temp_c": 25.8, "feelslike_c": 29.4, "humidity": 90, "wind_kph": 9.5,  "precip_mm": 1.2, "uv": 0.5, "condition": "Mist"}},

    # ── Thanjavur, Tamil Nadu (hot semi-arid, low rain) ────────────────────
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 0,
     "weather": {"temp_c": 27.0, "feelslike_c": 30.5, "humidity": 72, "wind_kph": 12.0, "precip_mm": 0.0, "uv": 3.5, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 1,
     "weather": {"temp_c": 31.5, "feelslike_c": 35.8, "humidity": 66, "wind_kph": 14.0, "precip_mm": 0.0, "uv": 7.5, "condition": "Sunny"}},
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 2,
     "weather": {"temp_c": 35.8, "feelslike_c": 40.2, "humidity": 58, "wind_kph": 16.0, "precip_mm": 0.0, "uv": 10.0, "condition": "Sunny"}},
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 3,
     "weather": {"temp_c": 34.0, "feelslike_c": 38.5, "humidity": 62, "wind_kph": 15.0, "precip_mm": 0.5, "uv": 6.5, "condition": "Partly cloudy"}},
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 4,
     "weather": {"temp_c": 31.2, "feelslike_c": 35.0, "humidity": 68, "wind_kph": 13.0, "precip_mm": 0.0, "uv": 1.0, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 5,
     "weather": {"temp_c": 29.0, "feelslike_c": 32.8, "humidity": 74, "wind_kph": 11.0, "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 6,
     "weather": {"temp_c": 26.8, "feelslike_c": 30.2, "humidity": 78, "wind_kph": 9.0,  "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Thanjavur", "slot": 7,
     "weather": {"temp_c": 27.5, "feelslike_c": 31.0, "humidity": 76, "wind_kph": 10.5, "precip_mm": 0.0, "uv": 1.0, "condition": "Clear"}},

    # ── Udupi, Karnataka (coastal, heavy monsoon) ──────────────────────────
    {"state": "Karnataka", "district": "Udupi", "slot": 0,
     "weather": {"temp_c": 25.0, "feelslike_c": 28.5, "humidity": 88, "wind_kph": 14.0, "precip_mm": 2.0, "uv": 2.5, "condition": "Mist"}},
    {"state": "Karnataka", "district": "Udupi", "slot": 1,
     "weather": {"temp_c": 28.2, "feelslike_c": 32.0, "humidity": 83, "wind_kph": 16.0, "precip_mm": 3.5, "uv": 5.5, "condition": "Patchy rain nearby"}},
    {"state": "Karnataka", "district": "Udupi", "slot": 2,
     "weather": {"temp_c": 31.0, "feelslike_c": 35.8, "humidity": 76, "wind_kph": 18.0, "precip_mm": 1.0, "uv": 8.0, "condition": "Partly cloudy"}},
    {"state": "Karnataka", "district": "Udupi", "slot": 3,
     "weather": {"temp_c": 29.5, "feelslike_c": 34.0, "humidity": 80, "wind_kph": 17.0, "precip_mm": 6.0, "uv": 5.0, "condition": "Moderate rain"}},
    {"state": "Karnataka", "district": "Udupi", "slot": 4,
     "weather": {"temp_c": 27.0, "feelslike_c": 30.8, "humidity": 86, "wind_kph": 15.0, "precip_mm": 8.5, "uv": 0.5, "condition": "Heavy rain"}},
    {"state": "Karnataka", "district": "Udupi", "slot": 5,
     "weather": {"temp_c": 25.5, "feelslike_c": 29.0, "humidity": 90, "wind_kph": 12.0, "precip_mm": 4.0, "uv": 0.0, "condition": "Patchy rain nearby"}},
    {"state": "Karnataka", "district": "Udupi", "slot": 6,
     "weather": {"temp_c": 24.2, "feelslike_c": 27.5, "humidity": 93, "wind_kph": 10.0, "precip_mm": 2.5, "uv": 0.0, "condition": "Overcast"}},
    {"state": "Karnataka", "district": "Udupi", "slot": 7,
     "weather": {"temp_c": 24.8, "feelslike_c": 28.2, "humidity": 91, "wind_kph": 12.0, "precip_mm": 1.8, "uv": 0.5, "condition": "Mist"}},

    # ── Kolhapur, Maharashtra (moderate, seasonal rain) ────────────────────
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 0,
     "weather": {"temp_c": 23.5, "feelslike_c": 25.8, "humidity": 72, "wind_kph": 10.0, "precip_mm": 0.0, "uv": 3.0, "condition": "Clear"}},
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 1,
     "weather": {"temp_c": 27.8, "feelslike_c": 30.5, "humidity": 65, "wind_kph": 12.0, "precip_mm": 0.0, "uv": 6.5, "condition": "Sunny"}},
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 2,
     "weather": {"temp_c": 33.2, "feelslike_c": 36.8, "humidity": 56, "wind_kph": 14.0, "precip_mm": 0.0, "uv": 9.5, "condition": "Sunny"}},
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 3,
     "weather": {"temp_c": 31.5, "feelslike_c": 35.0, "humidity": 60, "wind_kph": 13.0, "precip_mm": 1.5, "uv": 6.0, "condition": "Partly cloudy"}},
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 4,
     "weather": {"temp_c": 28.0, "feelslike_c": 31.5, "humidity": 68, "wind_kph": 11.0, "precip_mm": 3.0, "uv": 0.5, "condition": "Patchy rain nearby"}},
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 5,
     "weather": {"temp_c": 25.5, "feelslike_c": 28.0, "humidity": 74, "wind_kph": 9.0,  "precip_mm": 0.5, "uv": 0.0, "condition": "Clear"}},
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 6,
     "weather": {"temp_c": 22.8, "feelslike_c": 24.9, "humidity": 78, "wind_kph": 8.0,  "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Maharashtra", "district": "Kolhapur", "slot": 7,
     "weather": {"temp_c": 23.2, "feelslike_c": 25.4, "humidity": 76, "wind_kph": 9.5,  "precip_mm": 0.0, "uv": 1.0, "condition": "Clear"}},

    # ── Mandya, Karnataka (dry savanna) ───────────────────────────────────
    {"state": "Karnataka", "district": "Mandya", "slot": 0,
     "weather": {"temp_c": 22.8, "feelslike_c": 24.5, "humidity": 68, "wind_kph": 9.0,  "precip_mm": 0.0, "uv": 3.0, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Mandya", "slot": 1,
     "weather": {"temp_c": 27.5, "feelslike_c": 30.2, "humidity": 62, "wind_kph": 11.0, "precip_mm": 0.0, "uv": 6.5, "condition": "Sunny"}},
    {"state": "Karnataka", "district": "Mandya", "slot": 2,
     "weather": {"temp_c": 33.0, "feelslike_c": 36.5, "humidity": 53, "wind_kph": 13.0, "precip_mm": 0.0, "uv": 9.0, "condition": "Sunny"}},
    {"state": "Karnataka", "district": "Mandya", "slot": 3,
     "weather": {"temp_c": 31.2, "feelslike_c": 34.8, "humidity": 58, "wind_kph": 12.5, "precip_mm": 1.0, "uv": 5.5, "condition": "Partly cloudy"}},
    {"state": "Karnataka", "district": "Mandya", "slot": 4,
     "weather": {"temp_c": 27.8, "feelslike_c": 30.5, "humidity": 65, "wind_kph": 10.0, "precip_mm": 0.0, "uv": 0.5, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Mandya", "slot": 5,
     "weather": {"temp_c": 25.0, "feelslike_c": 27.2, "humidity": 70, "wind_kph": 8.5,  "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Mandya", "slot": 6,
     "weather": {"temp_c": 22.0, "feelslike_c": 23.8, "humidity": 74, "wind_kph": 7.5,  "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Mandya", "slot": 7,
     "weather": {"temp_c": 22.5, "feelslike_c": 24.2, "humidity": 72, "wind_kph": 8.5,  "precip_mm": 0.0, "uv": 0.5, "condition": "Clear"}},

    # ── Coimbatore, Tamil Nadu (dry, windy plateau) ────────────────────────
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 0,
     "weather": {"temp_c": 24.5, "feelslike_c": 26.8, "humidity": 65, "wind_kph": 16.0, "precip_mm": 0.0, "uv": 3.5, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 1,
     "weather": {"temp_c": 29.0, "feelslike_c": 32.5, "humidity": 58, "wind_kph": 18.0, "precip_mm": 0.0, "uv": 7.5, "condition": "Sunny"}},
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 2,
     "weather": {"temp_c": 34.5, "feelslike_c": 38.0, "humidity": 50, "wind_kph": 20.0, "precip_mm": 0.0, "uv": 10.0, "condition": "Sunny"}},
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 3,
     "weather": {"temp_c": 32.8, "feelslike_c": 36.2, "humidity": 54, "wind_kph": 19.0, "precip_mm": 0.5, "uv": 6.5, "condition": "Partly cloudy"}},
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 4,
     "weather": {"temp_c": 29.5, "feelslike_c": 33.0, "humidity": 60, "wind_kph": 17.0, "precip_mm": 0.0, "uv": 1.0, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 5,
     "weather": {"temp_c": 27.0, "feelslike_c": 30.0, "humidity": 66, "wind_kph": 15.0, "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 6,
     "weather": {"temp_c": 24.2, "feelslike_c": 26.5, "humidity": 70, "wind_kph": 13.0, "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Tamil Nadu", "district": "Coimbatore", "slot": 7,
     "weather": {"temp_c": 24.8, "feelslike_c": 27.2, "humidity": 68, "wind_kph": 14.5, "precip_mm": 0.0, "uv": 1.0, "condition": "Clear"}},

    # ── Indore, Madhya Pradesh (hot semi-arid, extreme summers) ───────────
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 0,
     "weather": {"temp_c": 28.0, "feelslike_c": 30.5, "humidity": 42, "wind_kph": 14.0, "precip_mm": 0.0, "uv": 4.0, "condition": "Clear"}},
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 1,
     "weather": {"temp_c": 33.5, "feelslike_c": 36.8, "humidity": 35, "wind_kph": 16.0, "precip_mm": 0.0, "uv": 8.0, "condition": "Sunny"}},
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 2,
     "weather": {"temp_c": 40.2, "feelslike_c": 43.5, "humidity": 25, "wind_kph": 18.0, "precip_mm": 0.0, "uv": 11.0, "condition": "Sunny"}},
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 3,
     "weather": {"temp_c": 38.0, "feelslike_c": 41.2, "humidity": 28, "wind_kph": 17.0, "precip_mm": 0.0, "uv": 7.5, "condition": "Sunny"}},
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 4,
     "weather": {"temp_c": 34.5, "feelslike_c": 37.8, "humidity": 33, "wind_kph": 15.0, "precip_mm": 0.0, "uv": 1.0, "condition": "Clear"}},
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 5,
     "weather": {"temp_c": 31.0, "feelslike_c": 33.8, "humidity": 38, "wind_kph": 13.0, "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 6,
     "weather": {"temp_c": 27.5, "feelslike_c": 29.8, "humidity": 44, "wind_kph": 11.0, "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Madhya Pradesh", "district": "Indore", "slot": 7,
     "weather": {"temp_c": 28.2, "feelslike_c": 30.6, "humidity": 43, "wind_kph": 12.5, "precip_mm": 0.0, "uv": 1.5, "condition": "Clear"}},

    # ── Nagpur, Maharashtra (hottest city, very dry) ───────────────────────
    {"state": "Maharashtra", "district": "Nagpur", "slot": 0,
     "weather": {"temp_c": 30.5, "feelslike_c": 33.0, "humidity": 35, "wind_kph": 12.0, "precip_mm": 0.0, "uv": 4.5, "condition": "Clear"}},
    {"state": "Maharashtra", "district": "Nagpur", "slot": 1,
     "weather": {"temp_c": 36.0, "feelslike_c": 39.5, "humidity": 28, "wind_kph": 14.0, "precip_mm": 0.0, "uv": 8.5, "condition": "Sunny"}},
    {"state": "Maharashtra", "district": "Nagpur", "slot": 2,
     "weather": {"temp_c": 42.5, "feelslike_c": 45.8, "humidity": 18, "wind_kph": 16.0, "precip_mm": 0.0, "uv": 12.0, "condition": "Sunny"}},
    {"state": "Maharashtra", "district": "Nagpur", "slot": 3,
     "weather": {"temp_c": 40.0, "feelslike_c": 43.2, "humidity": 21, "wind_kph": 15.0, "precip_mm": 0.0, "uv": 8.0, "condition": "Sunny"}},
    {"state": "Maharashtra", "district": "Nagpur", "slot": 4,
     "weather": {"temp_c": 36.5, "feelslike_c": 39.8, "humidity": 26, "wind_kph": 13.0, "precip_mm": 0.0, "uv": 1.5, "condition": "Clear"}},
    {"state": "Maharashtra", "district": "Nagpur", "slot": 5,
     "weather": {"temp_c": 33.0, "feelslike_c": 35.5, "humidity": 31, "wind_kph": 11.0, "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Maharashtra", "district": "Nagpur", "slot": 6,
     "weather": {"temp_c": 29.5, "feelslike_c": 31.8, "humidity": 37, "wind_kph": 9.0,  "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Maharashtra", "district": "Nagpur", "slot": 7,
     "weather": {"temp_c": 30.2, "feelslike_c": 32.6, "humidity": 36, "wind_kph": 11.0, "precip_mm": 0.0, "uv": 2.0, "condition": "Clear"}},

    # ── Dharwad, Karnataka (dry sub-humid plateau) ─────────────────────────
    {"state": "Karnataka", "district": "Dharwad", "slot": 0,
     "weather": {"temp_c": 23.0, "feelslike_c": 25.5, "humidity": 62, "wind_kph": 10.0, "precip_mm": 0.0, "uv": 3.0, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Dharwad", "slot": 1,
     "weather": {"temp_c": 28.5, "feelslike_c": 31.8, "humidity": 55, "wind_kph": 12.0, "precip_mm": 0.0, "uv": 7.0, "condition": "Sunny"}},
    {"state": "Karnataka", "district": "Dharwad", "slot": 2,
     "weather": {"temp_c": 35.0, "feelslike_c": 38.5, "humidity": 46, "wind_kph": 14.0, "precip_mm": 0.0, "uv": 9.5, "condition": "Sunny"}},
    {"state": "Karnataka", "district": "Dharwad", "slot": 3,
     "weather": {"temp_c": 33.0, "feelslike_c": 36.5, "humidity": 50, "wind_kph": 13.5, "precip_mm": 1.5, "uv": 6.0, "condition": "Partly cloudy"}},
    {"state": "Karnataka", "district": "Dharwad", "slot": 4,
     "weather": {"temp_c": 29.5, "feelslike_c": 32.8, "humidity": 57, "wind_kph": 12.0, "precip_mm": 0.5, "uv": 0.5, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Dharwad", "slot": 5,
     "weather": {"temp_c": 26.5, "feelslike_c": 29.0, "humidity": 63, "wind_kph": 10.0, "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Dharwad", "slot": 6,
     "weather": {"temp_c": 23.5, "feelslike_c": 25.8, "humidity": 67, "wind_kph": 8.5,  "precip_mm": 0.0, "uv": 0.0, "condition": "Clear"}},
    {"state": "Karnataka", "district": "Dharwad", "slot": 7,
     "weather": {"temp_c": 23.8, "feelslike_c": 26.2, "humidity": 65, "wind_kph": 9.5,  "precip_mm": 0.0, "uv": 1.0, "condition": "Clear"}},
]

def init_weather_mongo() -> tuple[bool, str]:
    try:
        client = MongoClient(MONGO_URI)
        collection = client[MONGO_DB][MONGO_COLLECTION]

        collection.create_index("district")
        collection.create_index("slot")
        collection.create_index(
            [("district", 1), ("slot", 1)],
            unique=True,
        )

        inserted = 0
        for record in WEATHER_RECORDS:
            result = collection.update_one(
                {"district": record["district"], "slot": record["slot"]},
                {"$setOnInsert": record},
                upsert=True,
            )
            if result.upserted_id is not None:
                inserted += 1

        total = collection.count_documents({})
        return True, f"Weather MongoDB ready ({total} records total, {inserted} new records inserted)."

    except Exception as exc:
        return False, f"Weather MongoDB init skipped: {exc}"

if __name__ == "__main__":
    success, message = init_weather_mongo()
    print(f"[WeatherMongo] {message}")

def drop_and_reseed() -> tuple[bool, str]:
    try:
        client = MongoClient(MONGO_URI)
        client[MONGO_DB][MONGO_COLLECTION].drop()
        print("[WeatherMongo] Dropped old weather_data collection.")
        return init_weather_mongo()
    except Exception as exc:
        return False, f"Reseed failed: {exc}"

if __name__ == "__main__":
    import sys
    if "--reseed" in sys.argv:
        success, message = drop_and_reseed()
    else:
        success, message = init_weather_mongo()
    print(f"[WeatherMongo] {message}")