"""
SMART AGRICULTURE AI
Agronomic Recommendation & Calculation Engine

Calculates target soil moisture, water deficit depth (mm), total water volume (Liters/m3),
optimal irrigation technique, and smart watering schedules.
"""

# Crop optimal soil moisture ranges (%) per growth stage
CROP_MOISTURE_TARGETS = {
    "Rice": {"Sowing": 45, "Vegetative": 55, "Flowering": 60, "Harvest": 30},
    "Wheat": {"Sowing": 35, "Vegetative": 40, "Flowering": 45, "Harvest": 25},
    "Maize": {"Sowing": 30, "Vegetative": 40, "Flowering": 45, "Harvest": 25},
    "Cotton": {"Sowing": 30, "Vegetative": 35, "Flowering": 40, "Harvest": 20},
    "Sugarcane": {"Sowing": 40, "Vegetative": 50, "Flowering": 55, "Harvest": 30},
    "Potato": {"Sowing": 35, "Vegetative": 45, "Flowering": 50, "Harvest": 25}
}

# Soil water retention coefficients & root zone depth (mm)
SOIL_METRICS = {
    "Clay": {"root_depth_mm": 500, "retention_factor": 1.2, "drainage": "Slow"},
    "Loamy": {"root_depth_mm": 450, "retention_factor": 1.0, "drainage": "Optimal"},
    "Sandy": {"root_depth_mm": 350, "retention_factor": 0.7, "drainage": "Fast"},
    "Silt": {"root_depth_mm": 400, "retention_factor": 1.1, "drainage": "Moderate"}
}

def generate_agronomic_recommendation(sensor_data, prediction, confidence):
    crop = sensor_data.get("Crop_Type", "Wheat")
    stage = sensor_data.get("Crop_Growth_Stage", "Vegetative")
    soil_type = sensor_data.get("Soil_Type", "Loamy")
    current_moisture = float(sensor_data.get("Soil_Moisture", 25))
    temp = float(sensor_data.get("Temperature_C", 25))
    humidity = float(sensor_data.get("Humidity", 60))
    rainfall = float(sensor_data.get("Rainfall_mm", 500))
    area_ha = float(sensor_data.get("Field_Area_hectare", 1.0))
    mulching = str(sensor_data.get("Mulching_Used", "No")).strip().capitalize() == "Yes"
    ph = float(sensor_data.get("Soil_pH", 6.5))
    ec = float(sensor_data.get("Electrical_Conductivity", 1.5))

    # Target moisture lookup
    crop_targets = CROP_MOISTURE_TARGETS.get(crop, {"Vegetative": 40})
    target_moisture = crop_targets.get(stage, crop_targets.get("Vegetative", 40))

    # Soil metrics lookup
    soil_info = SOIL_METRICS.get(soil_type, SOIL_METRICS["Loamy"])
    root_depth = soil_info["root_depth_mm"]

    # Calculate deficit %
    moisture_deficit_pct = max(0.0, target_moisture - current_moisture)

    # Adjust depth needed in mm based on prediction severity
    if prediction == "High":
        base_depth_mm = max(25.0, moisture_deficit_pct * 0.8)
    elif prediction == "Medium":
        base_depth_mm = max(10.0, moisture_deficit_pct * 0.4)
    else:  # Low
        base_depth_mm = 0.0 if current_moisture >= target_moisture else max(0.0, moisture_deficit_pct * 0.2)

    # Mulching savings reduction
    if mulching and base_depth_mm > 0:
        base_depth_mm *= 0.85  # 15% water savings due to reduced evapotranspiration

    # Evapotranspiration bonus if hot & dry
    if temp > 35 and humidity < 40 and base_depth_mm > 0:
        base_depth_mm *= 1.15  # 15% increase to offset high heat

    depth_mm = round(base_depth_mm, 1)

    # Volume calculation: 1 ha = 10,000 m^2. 1 mm of water = 1 L per m^2.
    # Volume (Liters) = area_ha * 10,000 * depth_mm
    total_liters = round(area_ha * 10000 * depth_mm)
    total_m3 = round(total_liters / 1000.0, 1)

    # Recommend irrigation system
    if crop in ["Sugarcane", "Cotton", "Potato"] or soil_type == "Sandy":
        rec_method = "Drip Irrigation (High Efficiency)"
        efficiency = "90-95%"
    elif crop in ["Wheat", "Maize"] and soil_type != "Sandy":
        rec_method = "Micro-Sprinkler / Pivot System"
        efficiency = "75-85%"
    elif crop == "Rice":
        rec_method = "Controlled Paddy Basin / Alternate Wetting & Drying (AWD)"
        efficiency = "70-80%"
    else:
        rec_method = "Precision Drip Line"
        efficiency = "85-90%"

    # Determine optimal timing
    if temp > 30:
        timing = "Early Morning (5:00 AM - 8:00 AM) or Evening (6:00 PM - 8:00 PM)"
        timing_note = "Prevents severe evaporation loss during midday heat peak."
    else:
        timing = "Morning (6:00 AM - 9:00 AM)"
        timing_note = "Allows optimal absorption with minimal thermal stress."

    # Specific Agronomic Alerts
    alerts = []
    if ph < 5.5:
        alerts.append("Soil is acidic (pH < 5.5). Consider agricultural lime application.")
    elif ph > 7.8:
        alerts.append("Soil is alkaline (pH > 7.8). Monitor micronutrient availability (Zinc/Iron).")

    if ec > 2.5:
        alerts.append("High Soil Salinity detected (EC > 2.5 dS/m). Ensure adequate leaching fraction.")

    if mulching:
        alerts.append("Mulching active: 15% reduced moisture evaporation achieved.")
    else:
        alerts.append("Tip: Applying organic mulch can save up to 15-20% irrigation water.")

    # Status summary message
    if prediction == "High":
        status_msg = f"Critical Moisture Deficit! Immediate irrigation of {depth_mm} mm (~{total_liters:,} Liters) recommended for {crop}."
    elif prediction == "Medium":
        status_msg = f"Moderate Moisture Level. Scheduled top-up of {depth_mm} mm (~{total_liters:,} Liters) recommended within 24-48 hours."
    else:
        status_msg = f"Optimal Soil Moisture ({current_moisture}%). No immediate irrigation required for {crop}."

    return {
        "prediction": prediction,
        "confidence": confidence,
        "target_moisture_pct": target_moisture,
        "current_moisture_pct": current_moisture,
        "moisture_deficit_pct": round(moisture_deficit_pct, 1),
        "irrigation_depth_mm": depth_mm,
        "total_liters": total_liters,
        "total_m3": total_m3,
        "field_area_ha": area_ha,
        "recommended_method": rec_method,
        "system_efficiency": efficiency,
        "optimal_timing": timing,
        "timing_note": timing_note,
        "status_message": status_msg,
        "soil_drainage": soil_info["drainage"],
        "agronomic_alerts": alerts
    }
