"""
SMART AGRICULTURE AI
Feature Mapper Service

Explicitly maps live ESP32 sensor telemetry and Farm Configuration
into the exact 16 feature names, order, and data types expected by the ML model.
"""

import pandas as pd
try:
    from src.config import MODEL_FEATURES, CATEGORICAL_CHOICES
except ImportError:
    from config import MODEL_FEATURES, CATEGORICAL_CHOICES



class FeatureMapper:
    @staticmethod
    def map_to_model_features(sensor_data, farm_data):
        """
        Maps ESP32 sensor payload + Farm config dictionary to 16 Model Features.
        
        Conceptual Mapping:
        -------------------
        ESP32 `soil_moisture`           -> Model `Soil_Moisture`
        ESP32 `temperature`             -> Model `Temperature_C`
        ESP32 `humidity`                -> Model `Humidity`
        ESP32 `rainfall`                -> Model `Rainfall_mm`
        ESP32 `sunlight`                -> Model `Sunlight_Hours`
        ESP32 `wind_speed`              -> Model `Wind_Speed_kmh`
        
        Farm Config `soil_type`         -> Model `Soil_Type`
        Farm Config `soil_ph`           -> Model `Soil_pH`
        Farm Config `organic_carbon`    -> Model `Organic_Carbon`
        Farm Config `electrical_conductivity` -> Model `Electrical_Conductivity`
        Farm Config `crop_type`         -> Model `Crop_Type`
        Farm Config `crop_growth_stage` -> Model `Crop_Growth_Stage`
        Farm Config `season`            -> Model `Season`
        Farm Config `field_area_hectare`-> Model `Field_Area_hectare`
        Farm Config `mulching_used`     -> Model `Mulching_Used`
        Farm Config `region`            -> Model `Region`
        """
        # Raw sunlight normalization if given in raw lux (e.g. 0-100000 lux mapped to 0-14 hours representation)
        raw_sunlight = float(sensor_data.get("sunlight", 7.5))
        if raw_sunlight > 24.0:
            # Documented normalization: convert lux to daylight hours representation
            sunlight_hours = min(14.0, max(4.0, (raw_sunlight / 100000.0) * 12.0 + 4.0))
        else:
            sunlight_hours = float(raw_sunlight)

        # Categorical Sanitization & Region Mapping
        raw_region = str(farm_data.get("region", "North")).strip().title()
        region_mapping = {
            "Maharashtra": "West", "Gujarat": "West", "Goa": "West", "Rajasthan": "West",
            "Punjab": "North", "Haryana": "North", "Delhi": "North", "UP": "North", "Uttar Pradesh": "North", "Himachal": "North",
            "Tamil Nadu": "South", "Kerala": "South", "Karnataka": "South", "Andhra Pradesh": "South", "Telangana": "South",
            "West Bengal": "East", "Odisha": "East", "Assam": "East", "Bihar": "East",
            "MP": "Central", "Madhya Pradesh": "Central", "Chhattisgarh": "Central"
        }
        if raw_region in CATEGORICAL_CHOICES["Region"]:
            mapped_region = raw_region
        else:
            mapped_region = region_mapping.get(raw_region, "West")

        mapped_dict = {
            "Soil_Type": str(farm_data.get("soil_type", "Loamy")).strip().capitalize(),
            "Soil_pH": float(farm_data.get("soil_ph", 6.5)),
            "Soil_Moisture": float(sensor_data.get("soil_moisture", 25.0)),
            "Organic_Carbon": float(farm_data.get("organic_carbon", 0.85)),
            "Electrical_Conductivity": float(farm_data.get("electrical_conductivity", 1.5)),
            "Temperature_C": float(sensor_data.get("temperature", 25.0)),
            "Humidity": float(sensor_data.get("humidity", 50.0)),
            "Rainfall_mm": float(sensor_data.get("rainfall", 0.0)),
            "Sunlight_Hours": float(sunlight_hours),
            "Wind_Speed_kmh": float(sensor_data.get("wind_speed", 10.0)),
            "Crop_Type": str(farm_data.get("crop_type", "Wheat")).strip().capitalize(),
            "Crop_Growth_Stage": str(farm_data.get("crop_growth_stage", "Vegetative")).strip().capitalize(),
            "Season": str(farm_data.get("season", "Rabi")).strip().capitalize(),
            "Field_Area_hectare": float(farm_data.get("field_area_hectare", farm_data.get("field_area", 2.5))),
            "Mulching_Used": str(farm_data.get("mulching_used", "No")).strip().capitalize(),
            "Region": mapped_region
        }


        # Capitalize mapping adjustments for categories (e.g. "Yes"/"No")
        if mapped_dict["Mulching_Used"] not in ["Yes", "No"]:
            mapped_dict["Mulching_Used"] = "Yes" if mapped_dict["Mulching_Used"].lower() in ["true", "1", "yes"] else "No"

        # Validate that all 16 features exist
        for feat in MODEL_FEATURES:
            if feat not in mapped_dict:
                raise KeyError(f"Feature Mapping failed: missing target feature '{feat}'")

        return mapped_dict
