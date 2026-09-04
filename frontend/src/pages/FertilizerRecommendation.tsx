import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Beaker, Sparkles } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Field'
import { Badge } from '@/components/ui/Badge'
import { IconBadge } from '@/components/ui/IconBadge'
import type { FertilizerRecommendation as FertilizerRecType } from '@/lib/types'

const NUTRIENT_TONE: Record<string, 'warning' | 'brand' | 'info'> = {
  Low: 'warning',
  Moderate: 'brand',
  High: 'info',
  Acidic: 'warning',
  'Suitable Range': 'brand',
  Alkaline: 'warning',
}

export default function FertilizerRecommendation() {
  const { t } = useTranslation()
  const [crop, setCrop] = useState('Rice')
  const [rec, setRec] = useState<FertilizerRecType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function fertilizerLabel(name: string) {
    const key = { Urea: 'fert_urea', Compost: 'fert_compost', 'Zinc Sulphate': 'fert_zinc_sulphate' }[name]
    return key ? t(`fertilizer.${key}`) : name
  }

  function statusLabel(status: string) {
    const key = {
      Low: 'irrigation.low',
      High: 'irrigation.high',
      Moderate: 'fertilizer.status_moderate',
      Acidic: 'fertilizer.status_acidic',
      'Suitable Range': 'fertilizer.status_suitable',
      Alkaline: 'fertilizer.status_alkaline',
    }[status]
    return key ? t(key) : status
  }

  async function getRecommendation() {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post<FertilizerRecType>('/api/fertilizer/recommend', { crop })
      setRec(data)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('fertilizer.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('fertilizer.subtitle')}</p>
      </div>

      <Card>
        <CardHeader title={t('fertilizer.recommended_fertilizer')} action={<IconBadge icon={<Beaker size={16} aria-hidden="true" />} tone="gold" />} />
        <div className="space-y-4 px-5 pb-5 pt-3">
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-40">
              <Select value={crop} onChange={(e) => setCrop(e.target.value)}>
                <option value="Rice">Rice</option>
                <option value="Sugarcane">Sugarcane</option>
              </Select>
            </div>
            <Button onClick={getRecommendation} isLoading={loading}>
              <Sparkles size={15} aria-hidden="true" /> {t('fertilizer.get_recommendation')}
            </Button>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          {rec && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gold-100 text-gold-700">
                  <Beaker size={28} aria-hidden="true" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{fertilizerLabel(rec.recommended_fertilizer)}</p>
                  <p className="text-sm text-[var(--text-secondary)]">{t('crop.model_confidence')}: {rec.model_probability}%</p>
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold text-[var(--text-secondary)]">{t('fertilizer.nutrient_status')}</p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <div className="rounded-xl border border-[var(--border-subtle)] p-3">
                    <p className="text-[11px] text-[var(--text-secondary)]">{t('sensors.nitrogen')}</p>
                    <Badge tone={NUTRIENT_TONE[rec.nutrient_status.nitrogen] ?? 'neutral'}>{statusLabel(rec.nutrient_status.nitrogen)}</Badge>
                  </div>
                  <div className="rounded-xl border border-[var(--border-subtle)] p-3">
                    <p className="text-[11px] text-[var(--text-secondary)]">{t('sensors.phosphorus')}</p>
                    <Badge tone={NUTRIENT_TONE[rec.nutrient_status.phosphorus] ?? 'neutral'}>{statusLabel(rec.nutrient_status.phosphorus)}</Badge>
                  </div>
                  <div className="rounded-xl border border-[var(--border-subtle)] p-3">
                    <p className="text-[11px] text-[var(--text-secondary)]">{t('sensors.potassium')}</p>
                    <Badge tone={NUTRIENT_TONE[rec.nutrient_status.potassium] ?? 'neutral'}>{statusLabel(rec.nutrient_status.potassium)}</Badge>
                  </div>
                  <div className="rounded-xl border border-[var(--border-subtle)] p-3">
                    <p className="text-[11px] text-[var(--text-secondary)]">{t('onboarding.soil_ph')}</p>
                    <Badge tone={NUTRIENT_TONE[rec.nutrient_status.soil_ph] ?? 'neutral'}>{statusLabel(rec.nutrient_status.soil_ph)}</Badge>
                  </div>
                </div>
              </div>

              <div>
                <p className="mb-1 text-xs font-semibold text-[var(--text-secondary)]">{t('fertilizer.why_recommendation')}</p>
                <p className="text-sm text-[var(--text-primary)]">{rec.reason}</p>
              </div>

              <Button variant="secondary" size="sm" onClick={getRecommendation} isLoading={loading}>
                <Sparkles size={14} aria-hidden="true" /> {t('fertilizer.get_recommendation')}
              </Button>
            </motion.div>
          )}
        </div>
      </Card>
    </div>
  )
}
