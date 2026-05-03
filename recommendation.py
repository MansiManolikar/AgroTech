from datetime import datetime, date

# Crop Stage Calculator
def get_crop_stage(planting_date, growth_duration: int) -> dict:
    if not planting_date or not growth_duration:
        return {"name": "Unknown", "index": 0, "days_elapsed": 0,
                "days_remaining": 0, "progress_pct": 0}

    if isinstance(planting_date, str):
        planting_date = datetime.strptime(planting_date, "%Y-%m-%d").date()

    today = date.today()
    days_elapsed = (today - planting_date).days
    days_remaining = max(0, growth_duration - days_elapsed)
    progress_pct = min(100, round((days_elapsed / growth_duration) * 100, 1))

    stage_pct = progress_pct / 100
    if stage_pct < 0.25:
        stage = {"name": "Seedling",           "index": 1,
                 "water_multiplier": 0.6,
                 "description": "Seedling establishment phase"}
    elif stage_pct < 0.50:
        stage = {"name": "Vegetative",         "index": 2,
                 "water_multiplier": 1.0,
                 "description": "Rapid leaf and stem development"}
    elif stage_pct < 0.75:
        stage = {"name": "Flowering",          "index": 3,
                 "water_multiplier": 1.3,
                 "description": "Critical water demand during flowering"}
    else:
        stage = {"name": "Harvest",            "index": 4,
                 "water_multiplier": 0.5,
                 "description": "Reduce water; prepare for harvest"}

    priority_map = {
        1: "Medium",
        2: "High",
        3: "Very High",
        4: "Low",
    }
    recommendation_map = {
        1: "Keep soil evenly moist while roots establish.",
        2: "Maintain regular irrigation and monitor moisture every 1-2 days.",
        3: "Prioritize timely irrigation; moisture stress can reduce yield.",
        4: "Reduce irrigation and prepare harvest checks.",
    }

    stage.update({
        "days_elapsed":    days_elapsed,
        "days_remaining":  days_remaining,
        "progress_pct":    progress_pct,
        "irrigation_priority": priority_map.get(stage["index"], "Monitor"),
        "recommendation": recommendation_map.get(stage["index"], "Monitor crop condition."),
        "irrigation_window": "Early morning or evening",
    })
    return stage

# Main Recommendation 
def generate_recommendation(farm: dict, crop: dict, soil_reading: dict,
                             weather: dict, forecast: list) -> dict:
    """
    Returns:
    {
        action          : str   — primary headline action
        priority        : str   — critical | warning | info | success
        color           : str   — hex color for UI
        icon            : str   — emoji
        reason          : str   — one-line summary
        details         : list  — bullet-point reasoning
        next_steps      : list  — ordered actionable steps
        alerts          : list  — urgent flags  { type, message }
        stage           : dict  — crop stage info
        scores          : dict  — sub-scores for transparency
    }
    """

    alerts     = []
    details    = []
    next_steps = []

    # 1. Crop Stage 
    planting_date    = farm.get("planting_date")
    growth_duration  = (crop or {}).get("growth_duration") or 120
    stage            = get_crop_stage(planting_date, growth_duration)
    water_mult       = stage.get("water_multiplier", 1.0)

    # 2. Soil Moisture
    soil_moisture    = None
    if soil_reading:
        soil_moisture = float(soil_reading.get("soil_moisture", 0))

    threshold        = float((crop or {}).get("moisture_threshold") or 35.0)
    adjusted_thresh  = threshold * water_mult          # stage-adjusted threshold
    critical_low     = adjusted_thresh - 15

    # Weather Parameters
    temp             = float((weather or {}).get("temp",        25))
    humidity         = float((weather or {}).get("humidity",    50))
    wind_kph         = float((weather or {}).get("wind_kph",     0))
    rainfall_mm      = float((weather or {}).get("rainfall_mm",  0))
    condition        = str((weather  or {}).get("condition",  "Clear"))
    uv_index         = float((weather or {}).get("uv_index",     0))

    rain_in_forecast = any(f.get("chance_of_rain", 0) >= 60 for f in forecast[:2])
    forecast_rain_mm = sum(f.get("total_rain", 0) for f in forecast[:2])

    # 4. Score Signal
    scores = {}

    # Moisture score (0–100; higher = drier / more urgent)
    if soil_moisture is not None:
        scores["moisture_urgency"] = round(
            max(0, min(100, ((adjusted_thresh - soil_moisture) / adjusted_thresh) * 100)), 1
        )
    else:
        scores["moisture_urgency"] = -1 

    scores["heat_stress"]    = round(max(0, (temp - 30) / 15 * 100), 1)      
    scores["wind_stress"]    = round(min(100, wind_kph / 50 * 100), 1)       
    scores["rain_relief"]    = round(min(100, (rainfall_mm / 25) * 100), 1)  
    scores["harvest_ready"]  = 1 if stage["index"] == 4 else 0

    # 5. Build Alerts
    if soil_moisture is not None and soil_moisture < critical_low:
        alerts.append({"type": "critical",
                        "message": f"🚨 Critical: Soil moisture {soil_moisture:.1f}% is dangerously low!"})

    if temp >= 40:
        alerts.append({"type": "critical",
                        "message": f"🌡️ Extreme heat {temp}°C — crops at risk of heat stress."})
    elif temp >= 35:
        alerts.append({"type": "warning",
                        "message": f"🌡️ High temperature {temp}°C — monitor closely."})

    if humidity > 85:
        alerts.append({"type": "warning",
                        "message": f"💧 High humidity {humidity}% — risk of fungal disease."})

    if wind_kph > 40:
        alerts.append({"type": "warning",
                        "message": f"💨 Strong winds {wind_kph} km/h — secure farm structures."})

    if uv_index >= 8:
        alerts.append({"type": "info",
                        "message": f"☀️ Very high UV index ({uv_index}) — avoid midday fieldwork."})

    if stage["index"] == 4 and stage["progress_pct"] >= 90:
        alerts.append({"type": "info",
                        "message": f"🌾 Crop at {stage['progress_pct']}% maturity — prepare harvest equipment."})

    # 6. Primary Recommendation Logic
    # PRIORITY 1: Harvest
    if stage["index"] == 4:
        if stage["progress_pct"] >= 95:
            action   = "Harvest Now"
            priority = "critical"
            color    = "#8B4513"
            icon     = "🌾"
            reason   = f"Crop is {stage['progress_pct']}% through its cycle — harvest immediately."
            details  = [
                f"Growth stage: {stage['name']} ({stage['progress_pct']}% complete)",
                f"Only {stage['days_remaining']} days left before over-ripening.",
                "Reduce or stop irrigation now to firm up produce.",
                "Check grain/fruit moisture content before harvest.",
            ]
            next_steps = [
                "Halt irrigation 3–5 days before harvest",
                "Inspect crop for ripeness indicators",
                "Arrange harvesting equipment and labor",
                "Plan post-harvest storage and transport",
            ]
        else:
            action   = "Prepare for Harvest"
            priority = "warning"
            color    = "#E65100"
            icon     = "🌾"
            reason   = f"Crop entering final maturity — {stage['days_remaining']} days to harvest."
            details  = [
                f"Growth stage: {stage['name']} ({stage['progress_pct']}% complete)",
                "Water requirements are reduced — minimal irrigation only.",
                "Monitor for pest pressure near harvest time.",
                "Reduce nitrogen inputs to avoid delayed maturity.",
            ]
            next_steps = [
                "Reduce irrigation frequency by 50%",
                "Monitor crop daily for harvest readiness signs",
                "Scout for late-season pests",
                "Begin sourcing harvest logistics",
            ]

    # PRIORITY 2: No soil data
    elif soil_moisture is None:
        action   = "Enter Soil Moisture"
        priority = "info"
        color    = "#607D8B"
        icon     = "📊"
        reason   = "No soil moisture data — please log today's reading to get recommendations."
        details  = [
            "Soil moisture is the primary driver of irrigation decisions.",
            f"Weather: {temp}°C, {condition}, Rainfall: {rainfall_mm} mm.",
            f"Crop stage: {stage['name']} — water multiplier {water_mult}×.",
        ]
        next_steps = [
            "Measure soil moisture with a probe or sensor",
            "Log your reading using the 'Log Soil Moisture' button",
            "Recommendations will auto-update after logging",
        ]

    # PRIORITY 3: Rain active / expected
    elif rainfall_mm > 15 or (rain_in_forecast and forecast_rain_mm > 20):
        action   = "Skip Irrigation"
        priority = "info"
        color    = "#1565C0"
        icon     = "🌧️"
        reason   = f"Sufficient rain detected/forecast ({rainfall_mm:.1f} mm now, {forecast_rain_mm:.1f} mm expected)."
        details  = [
            f"Current rainfall: {rainfall_mm} mm.",
            f"Forecast rain in next 48 hrs: {forecast_rain_mm:.1f} mm ({max(f.get('chance_of_rain',0) for f in forecast[:2])}% chance).",
            f"Soil moisture: {soil_moisture:.1f}% — check again after rain settles.",
            f"Crop stage: {stage['name']} — {stage['description']}.",
        ]
        next_steps = [
            "Skip scheduled irrigation for today",
            "Re-check soil moisture after 24 hours",
            "Ensure drainage channels are clear to prevent waterlogging",
            "Monitor for fungal issues in humid conditions",
        ]

    # PRIORITY 4: Critical moisture
    elif soil_moisture < critical_low:
        action   = "Irrigate Immediately"
        priority = "critical"
        color    = "#C62828"
        icon     = "🚨"
        reason   = f"Soil moisture {soil_moisture:.1f}% — critically below threshold {adjusted_thresh:.1f}%."
        details  = [
            f"Soil moisture ({soil_moisture:.1f}%) is {adjusted_thresh - soil_moisture:.1f}% below the adjusted threshold.",
            f"Crop stage: {stage['name']} — water demand multiplier {water_mult}×.",
            f"Temperature {temp}°C increases evapotranspiration demand.",
            "Delay risks yield loss or crop failure.",
        ]
        next_steps = [
            "Start irrigation within the next 2 hours",
            f"Apply irrigation for at least {60 if water_mult >= 1.0 else 30} minutes",
            "Re-check moisture 4 hours after irrigation",
            "Inspect crop for wilting or stress symptoms",
            "Consider shade netting if temperature > 38°C",
        ]

    # PRIORITY 5: Below threshold
    elif soil_moisture < adjusted_thresh:
        action   = "Schedule Irrigation"
        priority = "warning"
        color    = "#E65100"
        icon     = "📅"
        reason   = f"Soil moisture {soil_moisture:.1f}% below adjusted threshold {adjusted_thresh:.1f}%."
        details  = [
            f"Moisture is {adjusted_thresh - soil_moisture:.1f}% below the stage-adjusted threshold.",
            f"Stage '{stage['name']}' requires {water_mult}× water — threshold raised accordingly.",
            f"No significant rain forecast ({forecast_rain_mm:.1f} mm expected).",
            f"Current temperature: {temp}°C, humidity: {humidity}%.",
        ]
        next_steps = [
            "Schedule irrigation within the next 12–24 hours",
            "Prefer early morning (5–8 AM) or evening (5–7 PM) to minimize evaporation",
            "Avoid irrigation before predicted rainfall",
            "Re-check soil moisture after irrigation",
        ]

    # PRIORITY 6: Heat stress despite OK moisture
    elif temp >= 38 and soil_moisture < adjusted_thresh + 10:
        action   = "Increase Irrigation Frequency"
        priority = "warning"
        color    = "#F57F17"
        icon     = "🌡️"
        reason   = f"High temperature {temp}°C accelerates moisture loss — irrigate more frequently."
        details  = [
            f"Temperature {temp}°C raises crop water demand significantly.",
            f"Soil moisture {soil_moisture:.1f}% may drop below threshold faster than normal.",
            f"UV index {uv_index} — high evapotranspiration expected.",
            f"Wind speed {wind_kph} km/h adds to moisture loss.",
        ]
        next_steps = [
            "Increase irrigation frequency by 30%",
            "Irrigate during cooler parts of the day only",
            "Apply mulch around plant base to retain soil moisture",
            "Monitor leaf wilting as an early stress indicator",
            "Consider shade nets for sensitive crops",
        ]

    # PRIORITY 7: High humidity — disease risk
    elif humidity > 80 and rainfall_mm > 5:
        action   = "Disease Watch"
        priority = "warning"
        color    = "#6A1B9A"
        icon     = "🍄"
        reason   = f"High humidity {humidity}% with {rainfall_mm} mm rain — fungal disease risk elevated."
        details  = [
            f"Humidity {humidity}% combined with {rainfall_mm} mm rainfall creates disease-prone conditions.",
            "Fungal pathogens thrive above 80% humidity.",
            f"Soil moisture {soil_moisture:.1f}% is adequate — skip irrigation.",
            "Crop stage '{name}' has natural susceptibility to foliar disease.".format(**stage),
        ]
        next_steps = [
            "Skip irrigation — soil moisture is adequate",
            "Inspect leaves for early fungal or bacterial symptoms",
            "Apply preventive fungicide if susceptible crop",
            "Ensure adequate plant spacing for airflow",
            "Clear drainage to prevent waterlogging",
        ]

    # PRIORITY 8: All clear
    else:
        action   = "All Clear — Monitor"
        priority = "success"
        color    = "#2E7D32"
        icon     = "✅"
        reason   = f"Soil moisture {soil_moisture:.1f}% is optimal for {stage['name']} stage."
        details  = [
            f"Soil moisture {soil_moisture:.1f}% is within the optimal range for this stage.",
            f"Weather: {temp}°C, {condition} — no extreme conditions detected.",
            f"Forecast: {forecast_rain_mm:.1f} mm rain in next 48 hrs.",
            f"Crop stage: {stage['name']} — {stage['description']}.",
        ]
        next_steps = [
            "Continue normal irrigation schedule",
            "Log soil moisture again in 24–48 hours",
            "Inspect crop for pest or nutrient issues",
            "Review irrigation schedule for upcoming week",
        ]
        # Fertilizer advice by stage
        if stage["index"] == 1:
            next_steps.append("🌿 Fertilize: Apply Starter fertilizer (NPK 12-32-16) at 25 kg/acre for seedling establishment")
        elif stage["index"] == 2:
            next_steps.append("🌿 Fertilize: Apply Urea (46-0-0) at 30 kg/acre for vegetative growth — split into 2 doses")
        elif stage["index"] == 3:
            next_steps.append("🌿 Fertilize: Apply Potassium Sulphate (0-0-50) at 20 kg/acre to support flowering & fruit set")
        elif stage["index"] == 4:
            next_steps.append("🚫 Stop fertilizing — crop in maturity stage; excess nutrients reduce harvest quality")

    # 7. Add forecast advisory to details
    tomorrow = next((f for f in forecast if f.get("day_offset") == 1), None)
    if not tomorrow and len(forecast) > 1:
        tomorrow = forecast[1]
    if tomorrow:
        details.append(
            f"📅 Tomorrow: {tomorrow['condition']}, "
            f"max {tomorrow['max_temp']}°C, rain {tomorrow['total_rain']} mm "
            f"({tomorrow['chance_of_rain']}% chance)."
        )

    # Fertilizer advice based on stage
    fertilizer_advice = {
        1: {"name": "Starter Fertilizer (NPK 12-32-16)", "dose": "25 kg/acre", "timing": "At planting", "note": "Promotes root development"},
        2: {"name": "Urea (46-0-0)", "dose": "30 kg/acre", "timing": "Split into 2 applications", "note": "Boosts vegetative growth"},
        3: {"name": "Potassium Sulphate (0-0-50)", "dose": "20 kg/acre", "timing": "At flowering", "note": "Improves fruit set and quality"},
        4: {"name": "None — Stop fertilizing", "dose": "—", "timing": "—", "note": "Excess nutrients harm harvest quality"},
    }.get(stage.get("index", 0), {"name": "NPK 19-19-19", "dose": "20 kg/acre", "timing": "As required", "note": "General purpose"})

    return {
        "action":     action,
        "priority":   priority,
        "color":      color,
        "icon":       icon,
        "reason":     reason,
        "details":    details,
        "next_steps": next_steps,
        "alerts":     alerts,
        "stage":      stage,
        "scores":     scores,
        "fertilizer": fertilizer_advice,
        "weather":    {
            "temp": temp, "humidity": humidity, "wind_kph": wind_kph,
            "rainfall_mm": rainfall_mm, "condition": condition, "uv_index": uv_index,
        },
        "forecast": forecast,
    }