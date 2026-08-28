"""
SMART AGRICULTURE AI
AI Agronomist Agent Engine

Provides intelligent, context-aware interactive chat suggestions for farmers.
Ingests live ESP32 telemetry, farm configuration, and ML predictions to answer
queries on soil moisture deficits, watering schedules, heat risks, and soil health.
"""

import re


class AgronomistAgent:
    CROP_TARGETS = {
        "Rice": {"Sowing": 45, "Vegetative": 55, "Flowering": 60, "Harvest": 30},
        "Wheat": {"Sowing": 35, "Vegetative": 40, "Flowering": 45, "Harvest": 25},
        "Maize": {"Sowing": 30, "Vegetative": 40, "Flowering": 45, "Harvest": 25},
        "Cotton": {"Sowing": 30, "Vegetative": 35, "Flowering": 40, "Harvest": 20},
        "Sugarcane": {"Sowing": 40, "Vegetative": 50, "Flowering": 55, "Harvest": 30},
        "Potato": {"Sowing": 35, "Vegetative": 45, "Flowering": 50, "Harvest": 25}
    }

    @staticmethod
    def get_suggested_prompts():
        return [
            "💧 How much soil moisture does my crop need right now?",
            "⏰ When is the best time of day to irrigate?",
            "🌡️ How does current temperature and weather affect my farm?",
            "🧪 What soil treatment should I apply for my pH and EC?",
            "❓ Why did the AI predict this recommendation?"
        ]

    def process_query(self, user_query, sensor_data, farm_data, prediction_info=None):
        query_clean = user_query.lower().strip()

        # Extract parameters safely
        sm = float(sensor_data.get("soil_moisture", sensor_data.get("Soil_Moisture", 25.0)))
        temp = float(sensor_data.get("temperature", sensor_data.get("Temperature_C", 28.0)))
        humidity = float(sensor_data.get("humidity", sensor_data.get("Humidity", 55.0)))
        rainfall = float(sensor_data.get("rainfall", sensor_data.get("Rainfall_mm", 0.0)))
        wind = float(sensor_data.get("wind_speed", sensor_data.get("Wind_Speed_kmh", 10.0)))

        crop = str(farm_data.get("crop_type", farm_data.get("Crop_Type", "Wheat"))).strip().capitalize()
        stage = str(farm_data.get("crop_growth_stage", farm_data.get("Crop_Growth_Stage", "Vegetative"))).strip().capitalize()
        soil_type = str(farm_data.get("soil_type", farm_data.get("Soil_Type", "Loamy"))).strip().capitalize()
        ph = float(farm_data.get("soil_ph", farm_data.get("Soil_pH", 6.5)))
        ec = float(farm_data.get("electrical_conductivity", farm_data.get("Electrical_Conductivity", 1.5)))
        oc = float(farm_data.get("organic_carbon", farm_data.get("Organic_Carbon", 0.85)))
        area = float(farm_data.get("field_area_hectare", farm_data.get("field_area", 2.5)))
        mulch = str(farm_data.get("mulching_used", farm_data.get("Mulching_Used", "No"))).strip().capitalize() == "Yes"

        pred_class = "Medium"
        confidence = 100.0
        if prediction_info:
            pred_class = prediction_info.get("prediction", "Medium")
            confidence = prediction_info.get("confidence", 100.0)

        # Target moisture lookup
        crop_stage_targets = self.CROP_TARGETS.get(crop, {"Vegetative": 40})
        target_sm = crop_stage_targets.get(stage, crop_stage_targets.get("Vegetative", 40))
        deficit_pct = max(0.0, target_sm - sm)

        # Response routing
        response_text = ""
        action_bullets = []

        if any(w in query_clean for w in ["moisture", "water", "how much", "deficit", "liters", "volume"]):
            response_text = f"🌾 **Soil Moisture Analysis for {crop} ({stage} Stage):**\n"
            response_text += f"Your current soil moisture is **{sm:.1f}%**, while the optimal target for {crop} at the {stage} stage is **{target_sm}%**.\n"

            if deficit_pct > 0:
                depth_mm = round(deficit_pct * 0.6, 1)
                est_liters = round(area * 10000 * depth_mm)
                response_text += f"Your field has a moisture deficit of **{deficit_pct:.1f}%** (~{depth_mm} mm depth). For your **{area} hectare** field, approximately **{est_liters:,} Liters** ({round(est_liters/1000, 1)} m³) of water is needed to restore optimal root zone moisture."
                action_bullets.append(f"Irrigate to achieve target {target_sm}% soil moisture.")
                action_bullets.append("Use drip or micro-sprinkler to ensure uniform root absorption.")
            else:
                response_text += f"Your field is currently at or above the target moisture benchmark (**{sm:.1f}%** >= **{target_sm}%**). No additional watering is required right now."
                action_bullets.append("Hold irrigation to prevent root rot or nutrient leaching.")

        elif any(w in query_clean for w in ["when", "time", "schedule", "morning", "evening", "today"]):
            response_text = f"⏰ **Irrigation Schedule Recommendation:**\n"
            if temp > 30:
                response_text += f"With current temperatures at **{temp:.1f}°C**, irrigate during **Early Morning (5:00 AM – 8:00 AM)** or **Late Evening (6:00 PM – 8:00 PM)**.\n"
                response_text += "Midday peak sun leads to up to 30-40% evaporation loss before water reaches deep roots."
                action_bullets.append("Irrigate between 5:00 AM and 8:00 AM.")
                action_bullets.append("Avoid midday watering under high heat.")
            else:
                response_text += f"Under moderate temperatures (**{temp:.1f}°C**), morning irrigation (**6:00 AM – 9:00 AM**) is ideal.\n"
                action_bullets.append("Morning watering allows optimal uptake with minimal stress.")

        elif any(w in query_clean for w in ["temp", "heat", "weather", "wind", "humidity", "sun"]):
            response_text = f"🌡️ **Micro-Climate Impact Analysis:**\n"
            response_text += f"- **Temperature:** {temp:.1f}°C (" + ("Elevated heat risk" if temp > 32 else "Normal range") + ")\n"
            response_text += f"- **Humidity:** {humidity:.1f}% (" + ("Dry atmospheric condition" if humidity < 40 else "Normal") + ")\n"
            response_text += f"- **Wind Speed:** {wind:.1f} km/h (" + ("Higher surface drying rate" if wind > 15 else "Calm/Moderate") + ")\n"
            response_text += f"- **Rainfall:** {rainfall:.1f} mm\n"

            if temp > 32 and humidity < 40:
                response_text += "\nHigh temperatures combined with low air humidity create strong evapotranspiration demand, drying topsoil rapidly."
                action_bullets.append("Apply organic mulch or straw to protect topsoil from direct heat.")
                action_bullets.append("Increase monitoring frequency during heatwaves.")
            else:
                response_text += "\nWeather conditions are within manageable crop stress limits."
                action_bullets.append("Maintain regular moisture monitoring.")

        elif any(w in query_clean for w in ["ph", "ec", "salinity", "soil", "carbon", "treatment", "fertilizer"]):
            response_text = f"🧪 **Soil Health & Nutrient Analysis:**\n"
            response_text += f"- **Soil Type:** {soil_type}\n"
            response_text += f"- **pH Level:** {ph:.1f} (" + ("Acidic" if ph < 5.5 else ("Alkaline" if ph > 7.8 else "Optimal 6.0-7.5")) + ")\n"
            response_text += f"- **EC (Electrical Conductivity):** {ec:.1f} dS/m (" + ("High Salinity" if ec > 2.5 else "Normal") + ")\n"
            response_text += f"- **Organic Carbon:** {oc:.2f}%\n"

            if ph < 5.5:
                action_bullets.append("Soil is acidic (pH < 5.5): Apply agricultural lime or wood ash to raise pH.")
            elif ph > 7.8:
                action_bullets.append("Soil is alkaline (pH > 7.8): Apply agricultural sulfur or organic compost.")

            if ec > 2.5:
                action_bullets.append("High soil salinity (EC > 2.5 dS/m): Apply a leaching irrigation fraction to flush excess salts below the root zone.")

            if oc < 0.5:
                action_bullets.append("Low organic carbon (<0.5%): Incorporate green manure or well-rotted farmyard compost to improve moisture retention.")

        elif any(w in query_clean for w in ["why", "predict", "recommendation", "ai", "model", "confidence"]):
            response_text = f"🤖 **AI Model Prediction Breakdown:**\n"
            response_text += f"The trained Decision Tree Model predicted **{pred_class.upper()} Irrigation Requirement** with **{confidence:.1f}% Confidence**.\n\n"
            response_text += f"**Key Contributing Factors:**\n"
            response_text += f"1. **Soil Moisture:** {sm:.1f}% (Target: {target_sm}%)\n"
            response_text += f"2. **Temperature & Heat:** {temp:.1f}°C\n"
            response_text += f"3. **Cumulative Rainfall:** {rainfall:.1f} mm\n"
            response_text += f"4. **Crop Stage:** {crop} in {stage} stage\n"

            if mulch:
                response_text += "5. **Mulching Active:** Helps preserve topsoil moisture.\n"

            action_bullets.append(f"Follow {pred_class} requirement recommendations.")
            action_bullets.append("Re-evaluate as weather or sensor readings update.")

        else:
            response_text = f"🌾 **Smart Agriculture AI Agronomist Greeting:**\n"
            response_text += f"I am your AI Agronomist for your **{area} hectare {crop} field** ({stage} stage, {soil_type} soil).\n"
            response_text += f"Currently, your soil moisture is **{sm:.1f}%**, temperature is **{temp:.1f}°C**, and the AI model predicts **{pred_class.upper()} Irrigation Requirement** ({confidence:.1f}% confidence).\n\n"
            response_text += "Feel free to ask me anything about your water deficit, best watering times, soil pH/EC treatment, or crop protection!"

            action_bullets.append("Ask any specific farming question or select a quick prompt below.")

        return {
            "query": user_query,
            "response": response_text,
            "action_bullets": action_bullets,
            "field_context": {
                "crop": crop, "stage": stage, "soil_moisture": sm,
                "target_moisture": target_sm, "temperature": temp,
                "prediction": pred_class, "confidence": confidence
            }
        }
