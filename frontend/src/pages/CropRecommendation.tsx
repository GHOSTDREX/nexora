import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Wheat, Sparkles, Leaf } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { IconBadge } from '@/components/ui/IconBadge'
import { Dropdown } from '@/components/ui/Dropdown'
import type { CropRecommendation as CropRecType } from '@/lib/types'

const conditionTone: Record<string, 'brand' | 'warning' | 'critical' | 'neutral'> = {
  OPTIMAL: 'brand',
  WARNING: 'warning',
  CRITICAL: 'critical',
  NOT_EVALUATED: 'neutral',
}

// rice/sugarcane: hand-curated rules. Everything else: ranges derived from
// crop_recommendation.csv (see backend/app/ml/crop_condition/crop_condition_engine.py).
const CROP_LABELS: Record<string, string> = {
  rice: 'Rice',
  sugarcane: 'Sugarcane',
  apple: 'Apple',
  banana: 'Banana',
  blackgram: 'Black Gram',
  chickpea: 'Chickpea',
  coconut: 'Coconut',
  coffee: 'Coffee',
  cotton: 'Cotton',
  grapes: 'Grapes',
  jute: 'Jute',
  kidneybeans: 'Kidney Beans',
  lentil: 'Lentil',
  maize: 'Maize',
  mango: 'Mango',
  mothbeans: 'Moth Beans',
  mungbean: 'Mung Bean',
  muskmelon: 'Muskmelon',
  orange: 'Orange',
  papaya: 'Papaya',
  pigeonpeas: 'Pigeon Peas',
  pomegranate: 'Pomegranate',
  watermelon: 'Watermelon',
}
const CROP_OPTIONS = Object.entries(CROP_LABELS).sort((a, b) => a[1].localeCompare(b[1]))

interface ConditionResult {
  overall_condition: string
  summary: { optimal: number; warning: number; critical: number }
  parameters: Record<string, { value: number; status: string }>
}

export default function CropRecommendation() {
  const { t } = useTranslation()
  const [rec, setRec] = useState<CropRecType | null>(null)
  const [loadingRec, setLoadingRec] = useState(false)
  const [error, setError] = useState('')

  const [crop, setCrop] = useState('rice')
  const [condition, setCondition] = useState<ConditionResult | null>(null)
  const [loadingCondition, setLoadingCondition] = useState(false)

  async function getRecommendation() {
    setLoadingRec(true)
    setError('')
    try {
      const { data } = await api.get<CropRecType>('/api/crop/recommend')
      setRec(data)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoadingRec(false)
    }
  }

  async function checkCondition() {
    setLoadingCondition(true)
    try {
      const { data } = await api.post<ConditionResult>('/api/crop/condition', { crop })
      setCondition(data)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoadingCondition(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('crop.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('crop.subtitle')}</p>
      </div>

      <Card>
        <CardHeader title={t('crop.recommended_crop')} action={<IconBadge icon={<Wheat size={16} aria-hidden="true" />} tone="gold" />} />
        <div className="px-5 pb-5 pt-3">
          {!rec && (
            <Button onClick={getRecommendation} isLoading={loadingRec}>
              <Sparkles size={15} aria-hidden="true" /> {t('crop.get_recommendation')}
            </Button>
          )}

          {error && <p className="mt-2 text-sm text-red-400">{error}</p>}

          {rec && (
            <div>
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100 text-brand-700">
                  <Leaf size={28} aria-hidden="true" />
                </div>
                <div>
                  <p className="text-2xl font-bold capitalize text-[var(--text-primary)]">{rec.top_crop}</p>
                  <p className="text-sm text-[var(--text-secondary)]">{t('crop.model_confidence')}: {rec.confidence}%</p>
                </div>
              </motion.div>

              <p className="mb-2 mt-6 text-xs font-semibold text-[var(--text-secondary)]">{t('crop.other_suitable_crops')}</p>
              <div className="space-y-2.5">
                {rec.alternatives.map((alt) => (
                  <div key={alt.crop}>
                    <div className="mb-1 flex justify-between text-xs text-[var(--text-secondary)]">
                      <span className="capitalize">{alt.crop}</span>
                      <span>{alt.confidence}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-[var(--bg-surface-muted)]">
                      <motion.div
                        className="h-full rounded-full bg-brand-300"
                        initial={{ width: 0 }}
                        animate={{ width: `${alt.confidence}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <Button variant="secondary" size="sm" className="mt-5" onClick={getRecommendation} isLoading={loadingRec}>
                <Sparkles size={14} aria-hidden="true" /> {t('crop.get_recommendation')}
              </Button>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <CardHeader title={t('crop.condition_title')} action={<IconBadge icon={<Leaf size={16} aria-hidden="true" />} tone="brand" />} />
        <div className="space-y-4 px-5 pb-5 pt-3">
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-48">
              <Dropdown
                value={crop}
                onChange={setCrop}
                options={CROP_OPTIONS.map(([value, label]) => ({ value, label }))}
              />
            </div>
            <Button variant="secondary" onClick={checkCondition} isLoading={loadingCondition}>
              {t('crop.check_condition')}
            </Button>
          </div>

          {condition && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-[var(--text-secondary)]">{t('crop.overall_condition')}:</span>
                <Badge tone={conditionTone[condition.overall_condition] ?? 'neutral'}>
                  {t(`crop.${condition.overall_condition.toLowerCase()}`, condition.overall_condition)}
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {Object.entries(condition.parameters).map(([param, info]) => (
                  <div key={param} className="rounded-xl border border-[var(--border-subtle)] p-3">
                    <p className="text-[11px] text-[var(--text-secondary)]">{param.replace('_', ' ')}</p>
                    <p className="text-sm font-semibold text-[var(--text-primary)]">{info.value}</p>
                    <Badge tone={conditionTone[info.status] ?? 'neutral'}>
                      {t(`crop.${info.status.toLowerCase()}`, info.status)}
                    </Badge>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </Card>
    </div>
  )
}
