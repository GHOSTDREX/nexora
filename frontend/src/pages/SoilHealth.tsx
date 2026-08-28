import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { HeartPulse, Sparkles } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { IconBadge } from '@/components/ui/IconBadge'
import type { SoilHealth as SoilHealthType } from '@/lib/types'

const statusTone: Record<string, 'brand' | 'warning' | 'critical' | 'neutral'> = {
  Healthy: 'brand',
  'Moderate Stress': 'warning',
  'High Stress': 'critical',
  'Not evaluated': 'neutral',
}

export default function SoilHealth() {
  const { t } = useTranslation()
  const [result, setResult] = useState<SoilHealthType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function getAnalysis() {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get<SoilHealthType>('/api/soil-health/analyze')
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
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('soil_health.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('soil_health.subtitle')}</p>
      </div>

      <Card>
        <CardHeader title={t('soil_health.title')} action={<IconBadge icon={<HeartPulse size={16} aria-hidden="true" />} tone="brand" />} />
        <div className="px-5 pb-5 pt-3">
          {!result && (
            <Button onClick={getAnalysis} isLoading={loading}>
              <Sparkles size={15} aria-hidden="true" /> {t('soil_health.get_analysis')}
            </Button>
          )}

          {error && <p className="mt-2 text-sm text-red-400">{error}</p>}

          {result && (
            <div>
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100 text-brand-700">
                  <HeartPulse size={28} aria-hidden="true" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-[var(--text-secondary)]">{t('soil_health.overall_status')}:</span>
                    <Badge tone={statusTone[result.overall_status] ?? 'neutral'}>
                      {t(`soil_health.status_${result.overall_status.toLowerCase().replace(/ /g, '_')}`, result.overall_status)}
                    </Badge>
                  </div>
                  <p className="mt-1 text-2xl font-bold text-[var(--text-primary)]">
                    {result.health_score}
                    <span className="ml-1 text-sm font-medium text-[var(--text-secondary)]">/ 100</span>
                  </p>
                  <p className="text-xs text-[var(--text-secondary)]">{t('soil_health.health_score')}</p>
                </div>
              </motion.div>

              <p className="mt-3 text-xs text-[var(--text-secondary)]">{t('soil_health.scoring_note')}</p>

              <p className="mb-2 mt-4 text-xs font-semibold text-[var(--text-secondary)]">
                {result.primary_issue
                  ? `${t('soil_health.primary_issue')}: ${result.primary_issue}`
                  : t('soil_health.no_primary_issue')}
              </p>

              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {Object.entries(result.factors).map(([key, factor]) => (
                  <div key={key} className="rounded-xl border border-[var(--border-subtle)] p-3">
                    <p className="text-[11px] text-[var(--text-secondary)]">{t(`soil_health.factor_${key}`, factor.name)}</p>
                    <p className="text-sm font-semibold text-[var(--text-primary)]">
                      {factor.value === null ? '—' : factor.value}
                    </p>
                    <Badge tone={statusTone[factor.status] ?? 'neutral'}>
                      {t(`soil_health.status_${factor.status.toLowerCase().replace(/ /g, '_')}`, factor.status)}
                    </Badge>
                    {!factor.evaluated && (
                      <p className="mt-1 text-[10px] leading-snug text-[var(--text-secondary)]">
                        {t('soil_health.not_scored')}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-5 space-y-3">
                <div>
                  <p className="text-xs font-semibold text-[var(--text-secondary)]">{t('soil_health.explanation_title')}</p>
                  <p className="mt-1 text-sm text-[var(--text-primary)]">{result.explanation}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-[var(--text-secondary)]">{t('soil_health.recommendation_title')}</p>
                  <p className="mt-1 text-sm text-[var(--text-primary)]">{result.recommendation}</p>
                </div>
              </div>

              <Button variant="secondary" size="sm" className="mt-5" onClick={getAnalysis} isLoading={loading}>
                <Sparkles size={14} aria-hidden="true" /> {t('soil_health.get_analysis')}
              </Button>

              <p className="mt-4 text-[11px] text-[var(--text-secondary)]">{result.disclaimer}</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
