import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { TrendingUp, Sparkles } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input, Label } from '@/components/ui/Field'
import { IconBadge } from '@/components/ui/IconBadge'
import { Dropdown } from '@/components/ui/Dropdown'
import type { YieldPrediction as YieldPredictionType, YieldOptions } from '@/lib/types'

const CURRENT_YEAR = new Date().getFullYear()

export default function YieldPrediction() {
  const { t } = useTranslation()
  const { farm } = useAuth()

  const [options, setOptions] = useState<YieldOptions | null>(null)
  const [crop, setCrop] = useState('')
  const [state, setState] = useState('')
  const [season, setSeason] = useState('')
  const [year, setYear] = useState(String(CURRENT_YEAR))
  const [areaHectare, setAreaHectare] = useState('2.5')
  const [fertilizerKg, setFertilizerKg] = useState('50')
  const [pesticideKg, setPesticideKg] = useState('1')

  const [result, setResult] = useState<YieldPredictionType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get<YieldOptions>('/api/yield/options').then(({ data }) => {
      setOptions(data)
      setCrop(farm && data.crops.includes(farm.crop_type) ? farm.crop_type : data.crops[0])
      setSeason(farm && data.seasons.includes(farm.season) ? farm.season : data.seasons[0])
      setState(data.states[0])
    }).catch(() => {})
    if (farm) setAreaHectare(String(farm.field_area_hectare))
  }, [farm])

  async function predict() {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post<YieldPredictionType>('/api/yield/predict', {
        crop,
        state,
        season,
        year: Number(year),
        area_hectare: Number(areaHectare),
        fertilizer_kg: Number(fertilizerKg),
        pesticide_kg: Number(pesticideKg),
      })
      setResult(data)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('yield.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('yield.subtitle')}</p>
      </div>

      <Card>
        <CardHeader title={t('yield.form_title')} action={<IconBadge icon={<TrendingUp size={16} aria-hidden="true" />} tone="water" />} />
        <div className="space-y-4 px-5 pb-5 pt-3">
          {!options && <p className="text-sm text-[var(--text-secondary)]">{t('yield.loading')}</p>}

          {options && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div>
                <Label htmlFor="yield-crop">{t('yield.crop')}</Label>
                <Dropdown id="yield-crop" value={crop} onChange={setCrop} options={options.crops.map((c) => ({ value: c, label: c }))} />
              </div>
              <div>
                <Label htmlFor="yield-state">{t('yield.state')}</Label>
                <Dropdown id="yield-state" value={state} onChange={setState} options={options.states.map((s) => ({ value: s, label: s }))} />
              </div>
              <div>
                <Label htmlFor="yield-season">{t('yield.season')}</Label>
                <Dropdown id="yield-season" value={season} onChange={setSeason} options={options.seasons.map((s) => ({ value: s, label: s }))} />
              </div>
              <div>
                <Label htmlFor="yield-year">{t('yield.year')}</Label>
                <Input id="yield-year" type="number" value={year} onChange={(e) => setYear(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="yield-area">{t('yield.area_hectare')}</Label>
                <Input id="yield-area" type="number" step="0.1" value={areaHectare} onChange={(e) => setAreaHectare(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="yield-fertilizer">{t('yield.fertilizer_kg')}</Label>
                <Input id="yield-fertilizer" type="number" step="0.1" value={fertilizerKg} onChange={(e) => setFertilizerKg(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="yield-pesticide">{t('yield.pesticide_kg')}</Label>
                <Input id="yield-pesticide" type="number" step="0.1" value={pesticideKg} onChange={(e) => setPesticideKg(e.target.value)} />
              </div>
            </div>
          )}

          <Button onClick={predict} isLoading={loading} disabled={!options}>
            <Sparkles size={15} aria-hidden="true" /> {t('yield.predict')}
          </Button>

          {error && <p className="text-sm text-red-400">{error}</p>}

          {result && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-water-100 text-water-700">
                  <TrendingUp size={28} aria-hidden="true" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {result.predicted_yield} <span className="text-sm font-medium text-[var(--text-secondary)]">{t('yield.unit_per_ha')}</span>
                  </p>
                  <p className="text-sm text-[var(--text-secondary)]">{t('yield.predicted_for', { crop: result.crop, state: result.state, season: result.season, year: result.year })}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <div className="rounded-xl border border-[var(--border-subtle)] p-3">
                  <p className="text-[11px] text-[var(--text-secondary)]">{t('yield.estimated_total_production')}</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{result.estimated_total_production}</p>
                </div>
                <div className="rounded-xl border border-[var(--border-subtle)] p-3">
                  <p className="text-[11px] text-[var(--text-secondary)]">{t('yield.fertilizer_per_ha')}</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{result.fertilizer_per_ha} kg/ha</p>
                </div>
                <div className="rounded-xl border border-[var(--border-subtle)] p-3">
                  <p className="text-[11px] text-[var(--text-secondary)]">{t('yield.pesticide_per_ha')}</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{result.pesticide_per_ha} kg/ha</p>
                </div>
              </div>

              <Button variant="secondary" size="sm" onClick={predict} isLoading={loading}>
                <Sparkles size={14} aria-hidden="true" /> {t('yield.predict')}
              </Button>
            </motion.div>
          )}
        </div>
      </Card>
    </div>
  )
}
