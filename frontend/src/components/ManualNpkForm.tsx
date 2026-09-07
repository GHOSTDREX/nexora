import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FlaskConical, Save } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { Input, Label } from '@/components/ui/Field'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { IconBadge } from '@/components/ui/IconBadge'
import type { ManualNpkIn, SensorReading } from '@/lib/types'

// min/max mirror backend/app/schemas/sensor.py's ManualNpkIn field
// constraints exactly, same as ManualSensorForm's NUMERIC_FIELDS.
const FIELDS: { key: keyof ManualNpkIn; labelKey: string; unit: string; min: number; max: number }[] = [
  { key: 'soil_moisture', labelKey: 'sensors.soil_moisture', unit: '%', min: 0, max: 100 },
  { key: 'nitrogen', labelKey: 'sensors.nitrogen', unit: 'mg/kg', min: 0, max: 200 },
  { key: 'phosphorus', labelKey: 'sensors.phosphorus', unit: 'mg/kg', min: 0, max: 150 },
  { key: 'potassium', labelKey: 'sensors.potassium', unit: 'mg/kg', min: 0, max: 200 },
]

/** Quick-entry card for the farmer's handheld NPK/soil-moisture probe —
 * shown alongside live hardware temp/humidity/rain readings, not instead of
 * them (see ManualSensorForm for the full-replacement Manual sensor mode). */
export function ManualNpkForm({ initial }: { initial: SensorReading | null }) {
  const { t } = useTranslation()
  const [values, setValues] = useState<Record<string, string>>(() => ({
    soil_moisture: String(initial?.soil_moisture ?? 55),
    nitrogen: String(initial?.nitrogen ?? 80),
    phosphorus: String(initial?.phosphorus ?? 45),
    potassium: String(initial?.potassium ?? 60),
  }))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  async function submit() {
    setSaving(true)
    setError('')
    setSaved(false)

    const parsed: Record<string, number> = {}
    for (const f of FIELDS) {
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
      const payload: ManualNpkIn = {
        soil_moisture: parsed.soil_moisture,
        nitrogen: parsed.nitrogen,
        phosphorus: parsed.phosphorus,
        potassium: parsed.potassium,
      }
      await api.post('/api/sensors/manual-npk', payload)
      setSaved(true)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader title={t('dashboard.npk_probe_title')} action={<IconBadge icon={<FlaskConical size={16} aria-hidden="true" />} tone="amber" />} />
      <div className="space-y-3 px-5 pb-5 pt-3">
        <p className="text-xs text-[var(--text-secondary)]">{t('dashboard.npk_probe_hint')}</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {FIELDS.map((f) => (
            <div key={f.key} className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-3">
              <Label htmlFor={`npk-probe-${f.key}`}>{t(f.labelKey)}</Label>
              <div className="flex items-center gap-1.5">
                <Input
                  id={`npk-probe-${f.key}`}
                  type="number"
                  step="0.1"
                  min={f.min}
                  max={f.max}
                  value={values[f.key]}
                  onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                />
                <span className="shrink-0 text-xs text-[var(--text-secondary)]">{f.unit}</span>
              </div>
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex items-center gap-3">
          <Button onClick={submit} isLoading={saving} size="sm">
            <Save size={14} aria-hidden="true" /> {t('dashboard.submit_reading')}
          </Button>
          {saved && !saving && <span className="text-xs text-[var(--text-secondary)]">{t('dashboard.reading_saved')}</span>}
        </div>
      </div>
    </Card>
  )
}
