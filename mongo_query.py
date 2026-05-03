from __future__ import annotations
import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

MONGO_URI        = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB         = "agritech"
MONGO_COLLECTION = "weather_data"

SUPPORTED_DISTRICTS = [
    # Rice
    "Kuttanad", "Thanjavur", "Udupi", "Nagapattinam", "Dakshina Kannada",
    # Sugarcane
    "Kolhapur", "Mandya", "Satara", "Belagavi", "Coimbatore",
    # Soybean
    "Indore", "Nagpur", "Dharwad", "Ujjain", "Akola",
]

DISTRICT_STATE = {
    "Kuttanad":        "Kerala",
    "Thanjavur":       "Tamil Nadu",
    "Udupi":           "Karnataka",
    "Nagapattinam":    "Tamil Nadu",
    "Dakshina Kannada":"Karnataka",
    "Kolhapur":        "Maharashtra",
    "Mandya":          "Karnataka",
    "Satara":          "Maharashtra",
    "Belagavi":        "Karnataka",
    "Coimbatore":      "Tamil Nadu",
    "Indore":          "Madhya Pradesh",
    "Nagpur":          "Maharashtra",
    "Dharwad":         "Karnataka",
    "Ujjain":          "Madhya Pradesh",
    "Akola":           "Maharashtra",
}

IST = timezone(timedelta(hours=5, minutes=30))

def _col():
    return MongoClient(MONGO_URI)[MONGO_DB][MONGO_COLLECTION]

def _ist_now() -> datetime:
    return datetime.now(IST)

def _current_slot() -> int:
    h = _ist_now().hour
    if   6  <= h < 9:  return 0
    elif 9  <= h < 12: return 1
    elif 12 <= h < 15: return 2
    elif 15 <= h < 18: return 3
    elif 18 <= h < 21: return 4
    elif 21 <= h < 24: return 5
    elif 0  <= h < 3:  return 6
    else:              return 7

def _day_label(day: int) -> str:
    return (_ist_now() + timedelta(days=day)).strftime("%d %b")

def normalize_district(district: str) -> str:
    district = (district or "").strip().lower()
    for d in SUPPORTED_DISTRICTS:
        if d.lower() == district:
            return d
    for d in SUPPORTED_DISTRICTS:
        if d.lower() in district:
            return d
    return district.title() if district else ""

def district_from_location(location: str) -> str | None:
    norm = (location or "").strip().lower()
    for d in SUPPORTED_DISTRICTS:
        if d.lower() in norm:
            return d
    return None

def _get_day_slots(district: str, day: int) -> list[dict]:
    return list(
        _col()
        .find({"district": normalize_district(district), "day": day})
        .sort("slot", 1)
    )

def _get_slot(district: str, day: int, slot: int) -> dict | None:
    return _col().find_one({
        "district": normalize_district(district),
        "day": day,
        "slot": slot,
    })

def _fmt_current(record: dict | None) -> dict | None:
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

def _day_summary(district: str, day: int) -> dict | None:
    slots = _get_day_slots(district, day)
    if not slots:
        return None
    slot_map = {r["slot"]: r["weather"] for r in slots}
    peak  = slot_map.get(2, {})
    cold  = slot_map.get(6, {})
    total_rain = sum(s.get("precip_mm", 0) for s in slot_map.values())
    return {
        "day_offset":      day,
        "date":           _day_label(day),
        "max_temp":       peak.get("temp_c", 0),
        "min_temp":       cold.get("temp_c", 0),
        "avg_humidity":   round(sum(s.get("humidity", 0) for s in slot_map.values()) / len(slot_map)),
        "total_rain":     round(total_rain, 1),
        "condition":      peak.get("condition", "Unknown"),
        "chance_of_rain": 70 if total_rain > 0 else 20,
    }

def fetch_current_weather(location: str) -> dict | None:
    district = district_from_location(location or "")
    if not district:
        return None
    return _fmt_current(_get_slot(district, day=0, slot=_current_slot()))

def fetch_forecast(location: str, days: int = 3) -> list[dict]:
    district = district_from_location(location or "")
    if not district:
        return []
    return [s for s in (_day_summary(district, d) for d in range(0, days)) if s]

def fetch_recent_days(location: str) -> list[dict]:
    district = district_from_location(location or "")
    if not district:
        return []
    return [s for s in (_day_summary(district, d) for d in [-1, -2]) if s]

def get_slot_record(district: str, slot: int) -> dict | None:
    return _get_slot(normalize_district(district), day=0, slot=slot)

def get_all_district_slots(district: str) -> list[dict]:
    return _get_day_slots(normalize_district(district), day=0)

def current_slot() -> int:
    return _current_slot()