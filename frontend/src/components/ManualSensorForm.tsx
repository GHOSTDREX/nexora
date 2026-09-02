import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Save } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { Input, Label } from '@/components/ui/Field'
import { Button } from '@/components/ui/Button'
import { staggerContainer, staggerItem } from '@/lib/motion'
import type { ManualSensorReadingIn, SensorReading } from '@/lib/types'

// min/max mirror backend/app/schemas/sensor.py's ManualSensorReadingIn field
// constraints exactly — kept in sync so a submission never round-trips to a
// raw Pydantic validation error.
const NUMERIC_FIELDS: { key: keyof Omit<ManualSensorReadingIn, 'rain_detected'>; labelKey: string; unit: string; min: number; max: number }[] = [
  { key: 'temperature', labelKey: 'sensors.temperature', unit: '°C', min: -20, max: 70 },
  { key: 'humidity', labelKey: 'sensors.humidity', unit: '%', min: 0, max: 100 },
  { key: 'soil_moisture', labelKey: 'sensors.soil_moisture', unit: '%', min: 0, max: 100 },
  { key: 'nitrogen', labelKey: 'sensors.nitrogen', unit: 'mg/kg', min: 0, max: 200 },
  { key: 'phosphorus', labelKey: 'sensors.phosphorus', unit: 'mg/kg', min: 0, max: 150 },
  { key: 'potassium', labelKey: 'sensors.potassium', unit: 'mg/kg', min: 0, max: 200 },
  { key: 'wind_speed', labelKey: 'sensors.wind_speed', unit: 'km/h', min: 0, max: 150 },
]

export function ManualSensorForm({ initial }: { initial: SensorReading | null }) {
  const { t } = useTranslation()
  // Seeded once from the last live reading — deliberately not re-synced on
  // every latestReading change, or the form would fight the user's typing.
  const [values, setValues] = useState<Record<string, string>>(() => ({
    temperature: String(initial?.temperature ?? 28),
    humidity: String(initial?.humidity ?? 60),
    soil_moisture: String(initial?.soil_moisture ?? 55),
    nitrogen: String(initial?.nitrogen ?? 80),
    phosphorus: String(initial?.phosphorus ?? 45),
    potassium: String(initial?.potassium ?? 60),
    wind_speed: String(initial?.wind_speed ?? 10),
  }))
  const [rainDetected, setRainDetected] = useState(initial?.rain_detected ?? false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  async function submit() {
    setSaving(true)
    setError('')
    setSaved(false)

    const parsed: Record<string, number> = {}
    for (const f of NUMERIC_FIELDS) {
      const n = Number(values[f.key])
      if (values[f.key].trim() === '' || !Number.isFinite(n)) {
        setError(`${t(f.labelKey)}: enter a valid number.`)
        setSaving(false)
        return
      }
      if (n < f.min || n > f.max) {
        setError(`${t(f.labelKey)}: must be between ${f.min} and ${f.max}.`)
        setSaving(false)
        return
      }
      parsed[f.key] = n
    }

    try {
      const payload: ManualSensorReadingIn = {
        temperature: parsed.temperature,
        humidity: parsed.humidity,
        soil_moisture: parsed.soil_moisture,
        nitrogen: parsed.nitrogen,
        phosphorus: parsed.phosphorus,
        potassium: parsed.potassium,
        wind_speed: parsed.wind_speed,
        rain_detected: rainDetected,
      }
      await api.post('/api/sensors/manual', payload)
      setSaved(true)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4"
      >
        {NUMERIC_FIELDS.map((f) => (
          <motion.div
            key={f.key}
            variants={staggerItem}
            className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4"
          >
            <Label htmlFor={`manual-sensor-${f.key}`}>{t(f.labelKey)}</Label>
            <div className="flex items-center gap-1.5">
              <Input
                id={`manual-sensor-${f.key}`}
                type="number"
                step="0.1"
                min={f.min}
                max={f.max}
                value={values[f.key]}
                onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
              />
              <span className="shrink-0 text-xs text-[var(--text-secondary)]">{f.unit}</span>
            </div>
          </motion.div>
        ))}
        <motion.div variants={staggerItem} className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
          <Label>{t('sensors.rain_status')}</Label>
          <Button
            type="button"
            variant={rainDetected ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setRainDetected((r) => !r)}
            className="w-full"
          >
            {rainDetected ? t('sensors.rain_detected') : t('sensors.no_rain')}
          </Button>
        </motion.div>
      </motion.div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex items-center gap-3">
        <Button onClick={submit} isLoading={saving}>
          <Save size={14} aria-hidden="true" /> {t('dashboard.submit_reading')}
        </Button>
        {saved && !saving && <span className="text-xs text-[var(--text-secondary)]">{t('dashboard.reading_saved')}</span>}
      </div>
    </div>
  )
}
