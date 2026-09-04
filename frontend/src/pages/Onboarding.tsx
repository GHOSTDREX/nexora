import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Sprout } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { api, apiErrorMessage } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { FieldGroup, Input, Select } from '@/components/ui/Field'
import { LanguageDropdown } from '@/components/LanguageDropdown'
import { ThemeToggle } from '@/components/ThemeToggle'
import { REGIONS, SOIL_TYPES, CROP_TYPES, GROWTH_STAGES, SEASONS } from '@/lib/farmOptions'
import type { Farm } from '@/lib/types'

export default function Onboarding() {
  const { t } = useTranslation()
  const { setFarm } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const [form, setForm] = useState({
    name: 'My Farm',
    region: 'North',
    latitude: 28.6139,
    longitude: 77.209,
    field_area_hectare: 2.5,
    soil_type: 'Loamy',
    soil_ph: 6.5,
    organic_carbon: 0.85,
    electrical_conductivity: 1.5,
    crop_type: 'Wheat',
    crop_growth_stage: 'Vegetative',
    season: 'Rabi',
    mulching_used: 'No',
  })

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post<Farm>('/api/farm', form)
      setFarm(data)
      navigate('/dashboard')
    } catch (err) {
      setError(apiErrorMessage(err, t('common.error_generic')))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-[var(--bg-app)] to-sky-tint px-4 py-10">
      <div className="mx-auto flex max-w-2xl items-center justify-between pb-6">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500 text-brand-900">
            <Sprout size={18} aria-hidden="true" />
          </div>
          <span className="font-bold text-[var(--text-primary)]">{t('app_name')}</span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle compact />
          <LanguageDropdown />
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="mx-auto max-w-2xl rounded-3xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-8 shadow-xl shadow-brand-900/5"
      >
        <h1 className="text-lg font-bold text-[var(--text-primary)]">{t('onboarding.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('onboarding.subtitle')}</p>

        <form onSubmit={onSubmit} className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FieldGroup label={t('onboarding.farm_name')}>
            <Input required value={form.name} onChange={(e) => update('name', e.target.value)} />
          </FieldGroup>

          <FieldGroup label={t('onboarding.region')}>
            <Select value={form.region} onChange={(e) => update('region', e.target.value)}>
              {REGIONS.map((r) => (
                <option key={r} value={r}>{t(`options.region.${r}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.latitude')}>
            <Input
              type="number"
              step="any"
              value={form.latitude}
              onChange={(e) => update('latitude', Number(e.target.value))}
            />
          </FieldGroup>

          <FieldGroup label={t('onboarding.longitude')}>
            <Input
              type="number"
              step="any"
              value={form.longitude}
              onChange={(e) => update('longitude', Number(e.target.value))}
            />
          </FieldGroup>

          <FieldGroup label={t('onboarding.field_area')}>
            <Input
              type="number"
              step="any"
              min="0.01"
              value={form.field_area_hectare}
              onChange={(e) => update('field_area_hectare', Number(e.target.value))}
            />
          </FieldGroup>

          <FieldGroup label={t('onboarding.soil_type')}>
            <Select value={form.soil_type} onChange={(e) => update('soil_type', e.target.value)}>
              {SOIL_TYPES.map((s) => (
                <option key={s} value={s}>{t(`options.soil_type.${s}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.soil_ph')}>
            <Input
              type="number"
              step="any"
              min="3.5"
              max="10.5"
              value={form.soil_ph}
              onChange={(e) => update('soil_ph', Number(e.target.value))}
            />
          </FieldGroup>

          <FieldGroup label={t('onboarding.organic_carbon')}>
            <Input
              type="number"
              step="any"
              value={form.organic_carbon}
              onChange={(e) => update('organic_carbon', Number(e.target.value))}
            />
          </FieldGroup>

          <FieldGroup label={t('onboarding.electrical_conductivity')}>
            <Input
              type="number"
              step="any"
              value={form.electrical_conductivity}
              onChange={(e) => update('electrical_conductivity', Number(e.target.value))}
            />
          </FieldGroup>

          <FieldGroup label={t('onboarding.crop_type')}>
            <Select value={form.crop_type} onChange={(e) => update('crop_type', e.target.value)}>
              {CROP_TYPES.map((c) => (
                <option key={c} value={c}>{t(`options.crop_type.${c}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.crop_growth_stage')}>
            <Select value={form.crop_growth_stage} onChange={(e) => update('crop_growth_stage', e.target.value)}>
              {GROWTH_STAGES.map((g) => (
                <option key={g} value={g}>{t(`options.growth_stage.${g}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.season')}>
            <Select value={form.season} onChange={(e) => update('season', e.target.value)}>
              {SEASONS.map((s) => (
                <option key={s} value={s}>{t(`options.season.${s}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.mulching_used')}>
            <Select value={form.mulching_used} onChange={(e) => update('mulching_used', e.target.value)}>
              <option value="Yes">{t('common.yes')}</option>
              <option value="No">{t('common.no')}</option>
            </Select>
          </FieldGroup>

          {error && <p className="sm:col-span-2 text-sm text-red-400">{error}</p>}

          <Button type="submit" className="sm:col-span-2" isLoading={loading}>
            {loading ? t('onboarding.submitting') : t('onboarding.complete')}
          </Button>
        </form>
      </motion.div>
    </div>
  )
}
