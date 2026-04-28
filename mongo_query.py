from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta

from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB  = "agritech"
MONGO_COLLECTION = "weather_data"

SUPPORTED_DISTRICTS = (
    "Kuttanad",
    "Thanjavur",
    "Udupi",
    "Kolhapur",
    "Mandya",
    "Coimbatore",
    "Indore",
    "Nagpur",
    "Dharwad",
)

_SLOT_START_HOURS = [6, 9, 12, 15, 18, 21, 0, 3] 

def _get_collection():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB][MONGO_COLLECTION]

def _current_ist_hour() -> int:    
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).hour


def current_slot() -> int:
    h = _current_ist_hour()
    if   6  <= h < 9:  return 0
    elif 9  <= h < 12: return 1
    elif 12 <= h < 15: return 2
    elif 15 <= h < 18: return 3
    elif 18 <= h < 21: return 4
    elif 21 <= h < 24: return 5
    elif 0  <= h < 3:  return 6
    else:              return 7   

def normalize_district(district: str) -> str:
    district = (district or "").strip().lower()
    for supported in SUPPORTED_DISTRICTS:
        if supported.lower() == district:
            return supported
    for supported in SUPPORTED_DISTRICTS:
        if supported.lower() in district:
            return supported
    return district.title() if district else ""

def district_from_location(location: str) -> str | None:
    normalized = (location or "").strip().lower()
    for district in SUPPORTED_DISTRICTS:
        if district.lower() in normalized:
            return district
    return None

def get_slot_record(district: str, slot: int) -> dict | None:
    doc = _get_collection().find_one(
        {"district": normalize_district(district), "slot": slot}
    )
    return doc

def get_all_district_slots(district: str) -> list[dict]:
    docs = list(
        _get_collection()
        .find({"district": normalize_district(district)})
        .sort("slot", 1)
    )
    return docs

def _format_current(record: dict | None) -> dict | None:
    if not record:
        return None
    w = record.get("weather", {})
    return {
        "temp_c":      w.get("temp_c"),
        "feelslike_c": w.get("feelslike_c", w.get("temp_c")),
        "humidity":    w.get("humidity"),
        "wind_kph":    w.get("wind_kph", 0),
        "precip_mm":   w.get("precip_mm", 0),
        "uv":          w.get("uv", 0),
        "condition":   w.get("condition", "Unknown"),
    }


def _slot_to_label(slot: int) -> str:
    starts = ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00", "00:00", "03:00"]
    ends   = ["09:00", "12:00", "15:00", "18:00", "21:00", "00:00", "03:00", "06:00"]
    return f"{starts[slot]}–{ends[slot]}"

def _format_forecast_slot(record: dict) -> dict:
    w = record.get("weather", {})
    slot = record.get("slot", 0)
    temp_c = w.get("temp_c", 0)
    return {
        "date":           _slot_to_label(slot),
        "max_temp":       temp_c,
        "min_temp":       round(temp_c - 3, 1),
        "avg_humidity":   w.get("humidity", 0),
        "total_rain":     w.get("precip_mm", 0),
        "condition":      w.get("condition", "Unknown"),
        "chance_of_rain": 70 if (w.get("precip_mm") or 0) > 0 else 20,
    }

def fetch_current_weather(location: str) -> dict | None:
    district = district_from_location(location or "")
    if not district:
        return None
    slot = current_slot()
    record = get_slot_record(district, slot)
    return _format_current(record)


def fetch_forecast(location: str, days: int = 3) -> list[dict]:
    district = district_from_location(location or "")
    if not district:
        return []

    all_slots = get_all_district_slots(district)
    if not all_slots:
        return []

    # Build a slot->record map
    slot_map = {r["slot"]: r for r in all_slots}

    slot = current_slot()
    result = []
    for i in range(1, days + 1):
        next_slot = (slot + i) % 8
        rec = slot_map.get(next_slot)
        if rec:
            result.append(_format_forecast_slot(rec))

    return result