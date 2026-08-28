import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Droplets, RefreshCw, HelpCircle, BarChart3 } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { IconBadge } from '@/components/ui/IconBadge'
import type { Farm, IrrigationPrediction } from '@/lib/types'

const predictionTone: Record<string, 'brand' | 'warning' | 'critical'> = {
  Low: 'brand',
  Medium: 'warning',
  High: 'critical',
}

export default function Irrigation() {
  const { t } = useTranslation()
  const { farm, setFarm } = useAuth()
  const [prediction, setPrediction] = useState<IrrigationPrediction | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [switching, setSwitching] = useState(false)
  const [error, setError] = useState('')

  function load() {
    setLoading(true)
    api
      .get<IrrigationPrediction>('/api/irrigation/predict')
      .then(({ data }) => setPrediction(data))
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function refresh() {
    setRefreshing(true)
    setError('')
    try {
      const { data } = await api.get<IrrigationPrediction>('/api/irrigation/predict')
      setPrediction(data)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setRefreshing(false)
    }
  }

  async function toggleMode() {
    if (!farm) return
    setSwitching(true)
    try {
      const nextMode = farm.irrigation_mode === 'Auto' ? 'Manual' : 'Auto'
      const { data } = await api.patch<Farm>('/api/farm/irrigation-mode', { irrigation_mode: nextMode })
      setFarm(data)
    } finally {
      setSwitching(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('irrigation.title')}</h1>
        <div className="flex items-center gap-2">
          <Badge tone={farm?.irrigation_mode === 'Auto' ? 'brand' : 'neutral'}>{farm?.irrigation_mode === 'Auto' ? t('common.auto') : t('common.manual')}</Badge>
          <Button variant="secondary" size="sm" onClick={toggleMode} isLoading={switching}>
            {farm?.irrigation_mode === 'Auto' ? t('irrigation.set_manual') : t('irrigation.set_auto')}
          </Button>
        </div>
      </div>

      {farm?.irrigation_mode === 'Manual' && (
        <p className="rounded-xl bg-amber-50 px-4 py-2.5 text-sm text-amber-800">{t('irrigation.manual_hint')}</p>
      )}

      {loading ? (
        <Skeleton className="h-48 w-full" />
      ) : prediction ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardHeader title={t('irrigation.prediction')} action={<IconBadge icon={<Droplets size={16} aria-hidden="true" />} tone="water" />} />
            <div className="px-5 pb-5 pt-3 text-center">
              <motion.div
                key={prediction.prediction}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="py-3"
              >
                <Badge tone={predictionTone[prediction.prediction] ?? 'neutral'}>
                  {t(`irrigation.${prediction.prediction.toLowerCase()}`)}
                </Badge>
                <p className="mt-3 text-3xl font-bold text-[var(--text-primary)]">{prediction.confidence}%</p>
                <p className="text-xs text-[var(--text-secondary)]">{t('irrigation.confidence')}</p>
              </motion.div>
              <Button variant="secondary" size="sm" onClick={refresh} isLoading={refreshing} className="w-full">
                <RefreshCw size={14} aria-hidden="true" /> {t('irrigation.get_prediction')}
              </Button>
            </div>
          </Card>

          <Card className="lg:col-span-1">
            <CardHeader title={t('irrigation.probabilities')} action={<IconBadge icon={<BarChart3 size={16} aria-hidden="true" />} tone="gold" />} />
            <div className="space-y-3 px-5 pb-5 pt-3">
              {Object.entries(prediction.probabilities).map(([cls, prob]) => (
                <div key={cls}>
                  <div className="mb-1 flex justify-between text-xs text-[var(--text-secondary)]">
                    <span>{t(`irrigation.${cls.toLowerCase()}`, cls)}</span>
                    <span>{Math.round(prob * 100)}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-[var(--bg-surface-muted)]">
                    <motion.div
                      className="h-full rounded-full bg-brand-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${prob * 100}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="lg:col-span-1">
            <CardHeader title={t('irrigation.decision_support')} action={<IconBadge icon={<HelpCircle size={16} aria-hidden="true" />} tone="neutral" />} />
            <ul className="space-y-2 px-5 pb-5 pt-3 text-sm text-[var(--text-secondary)]">
              {prediction.indicators.length === 0 ? (
                <li>—</li>
              ) : (
                prediction.indicators.map((ind, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-400" />
                    {ind}
                  </li>
                ))
              )}
            </ul>
          </Card>
        </div>
      ) : (
        <p className="text-sm text-red-400">{error}</p>
      )}
    </div>
  )
}
