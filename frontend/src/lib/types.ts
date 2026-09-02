export interface User {
  id: number
  full_name: string
  email: string
  preferred_language: string
}

export interface Farm {
  id: number
  name: string
  region: string
  latitude: number
  longitude: number
  field_area_hectare: number
  soil_type: string
  soil_ph: number
  organic_carbon: number
  electrical_conductivity: number
  crop_type: string
  crop_growth_stage: string
  season: string
  mulching_used: string
  irrigation_mode: 'Auto' | 'Manual'
  sensor_mode: 'Auto' | 'Manual'
  hardware_enabled: boolean
  sensor_node_host: string
  robot_host: string
  camera_host: string
}

export interface SensorReading {
  id: number
  device_id: string
  timestamp: string
  soil_moisture: number
  temperature: number
  humidity: number
  rainfall: number
  sunlight: number
  wind_speed: number
  nitrogen: number
  phosphorus: number
  potassium: number
  rain_detected: boolean
  status: string
}

export interface ManualSensorReadingIn {
  temperature: number
  humidity: number
  soil_moisture: number
  nitrogen: number
  phosphorus: number
  potassium: number
  wind_speed: number
  rain_detected: boolean
}

export interface IrrigationPrediction {
  prediction: 'Low' | 'Medium' | 'High'
  confidence: number
  probabilities: Record<string, number>
  mapped_features: Record<string, string | number>
  indicators: string[]
  timestamp: string
}

export interface CropRecommendation {
  top_crop: string
  confidence: number
  alternatives: { crop: string; confidence: number }[]
  input_features: Record<string, number>
}

export interface FertilizerRecommendation {
  crop: string
  recommended_fertilizer: string
  model_probability: number
  nutrient_status: { nitrogen: string; phosphorus: string; potassium: string; soil_ph: string }
  reason: string
  input_features: Record<string, string | number>
  warnings: string[]
  timestamp: string
}

export interface YieldPrediction {
  crop: string
  state: string
  season: string
  year: number
  area_hectare: number
  predicted_yield: number
  estimated_total_production: number
  fertilizer_per_ha: number
  pesticide_per_ha: number
  warnings: string[]
  timestamp: string
}

export interface YieldOptions {
  crops: string[]
  states: string[]
  seasons: string[]
}

export interface SoilHealthFactor {
  name: string
  value: number | null
  status: string
  evaluated: boolean
  reason: string
}

export interface SoilHealth {
  overall_status: string
  health_score: number
  factors: Record<string, SoilHealthFactor>
  stress_factors: string[]
  primary_issue: string | null
  recommendation: string
  explanation: string
  rule_version: string
  rule_source: string
  disclaimer: string
  timestamp: string
}

export interface RobotStatus {
  robot_connected: boolean
  robot_battery_pct: number
  pump_on: boolean
  motor_speed: number
  irrigation_mode: string
  camera_pan_deg: number
  camera_tilt_deg: number
}

export interface RobotActionLog {
  action_type: string
  detail: Record<string, unknown>
  source: string
  timestamp: string
}

export interface CameraFrame {
  image_data_url: string
  pan_deg: number
  tilt_deg: number
  timestamp: string
  stream_url?: string | null
}

export interface CameraSnapshot extends CameraFrame {
  id: number
}

export interface AlertItem {
  id: number
  code: string
  severity: 'info' | 'warning' | 'critical'
  params: Record<string, unknown>
  is_read: boolean
  created_at: string
}

export interface WeatherToday {
  temperature_c: number
  humidity_pct: number
  rain_probability_pct: number
  wind_speed_kmh: number
  condition: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  created_at: string
}
