import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Bug, Upload, ImageUp, CheckCircle2, AlertTriangle, XCircle, ExternalLink } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { IconBadge } from '@/components/ui/IconBadge'
import type { DiseasePrediction } from '@/lib/types'

const STATE_TONE: Record<DiseasePrediction['decision_state'], 'brand' | 'warning' | 'critical'> = {
  accepted: 'brand',
  uncertain: 'warning',
  image_unsuitable: 'critical',
  subject_unsuitable: 'critical',
}

export default function DiseaseDetection() {
  const { t } = useTranslation()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<DiseasePrediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function pickFile(f: File | null) {
    setResult(null)
    setError('')
    setFile(f)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(f ? URL.createObjectURL(f) : null)
  }

  async function analyze() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post<DiseasePrediction>('/api/disease/predict', form)
      setResult(data)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const StateIcon = result?.decision_state === 'accepted' ? CheckCircle2 : result?.decision_state === 'uncertain' ? AlertTriangle : XCircle

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('disease.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('disease.subtitle')}</p>
      </div>

      <Card>
        <CardHeader title={t('disease.upload_title')} action={<IconBadge icon={<Bug size={16} aria-hidden="true" />} tone="brand" />} />
        <div className="space-y-4 px-5 pb-5 pt-3">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />

          {preview ? (
            <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)]">
              <img src={preview} alt={t('disease.upload_title')} className="max-h-80 w-full object-contain bg-[var(--bg-surface-muted)]" />
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-[var(--border-subtle)] py-10 text-[var(--text-secondary)] transition-colors hover:border-brand-300 hover:text-brand-700"
            >
              <ImageUp size={28} aria-hidden="true" />
              <span className="text-sm font-medium">{t('disease.choose_photo')}</span>
              <span className="text-xs">{t('disease.upload_hint')}</span>
            </button>
          )}

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
              <Upload size={14} aria-hidden="true" /> {preview ? t('disease.choose_different') : t('disease.choose_photo')}
            </Button>
            <Button type="button" size="sm" onClick={analyze} disabled={!file} isLoading={loading}>
              {t('disease.analyze')}
            </Button>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>
      </Card>

      {result && (
        <Card>
          <CardHeader
            title={t('disease.result_title')}
            action={<Badge tone={STATE_TONE[result.decision_state]} dot>{t(`disease.state_${result.decision_state}`)}</Badge>}
          />
          <div className="space-y-4 px-5 pb-5 pt-3">
            <div className="flex items-start gap-3 rounded-xl bg-[var(--bg-surface-muted)] p-4">
              <StateIcon size={20} className={result.decision_state === 'accepted' ? 'text-brand-600' : result.decision_state === 'uncertain' ? 'text-gold-600' : 'text-red-500'} aria-hidden="true" />
              <div>
                {result.accepted ? (
                  <p className="text-lg font-bold text-[var(--text-primary)]">{result.display_name}</p>
                ) : (
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{result.decision_message}</p>
                )}
                <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
                  {t('disease.confidence')}: {(result.confidence * 100).toFixed(1)}%
                </p>
                {result.guidance.length > 0 && (
                  <ul className="mt-2 list-inside list-disc space-y-0.5 text-xs text-[var(--text-secondary)]">
                    {result.guidance.map((g, i) => <li key={i}>{g}</li>)}
                  </ul>
                )}
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{t('disease.top_matches')}</p>
              <div className="space-y-2">
                {result.top3.map((c) => (
                  <div key={c.class} className="flex items-center gap-3 text-sm">
                    <span className="w-40 shrink-0 truncate text-[var(--text-primary)]">{c.display_name}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--bg-surface-muted)]">
                      <div className="h-full rounded-full bg-brand-500" style={{ width: `${c.confidence * 100}%` }} />
                    </div>
                    <span className="w-12 shrink-0 text-right text-xs text-[var(--text-secondary)]">{(c.confidence * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>

            {result.recommendation && (
              <div className="space-y-3 rounded-xl border border-[var(--border-subtle)] p-4">
                <p className="text-sm text-[var(--text-primary)]">{result.recommendation.short_description}</p>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{t('disease.symptoms')}</p>
                  <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-[var(--text-secondary)]">
                    {result.recommendation.common_symptoms.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{t('disease.management')}</p>
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">{result.recommendation.management}</p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{t('disease.prevention')}</p>
                  <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-[var(--text-secondary)]">
                    {result.recommendation.prevention.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </div>

                <a
                  href={result.recommendation.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline"
                >
                  {t('disease.source')}: {result.recommendation.source_name} <ExternalLink size={12} aria-hidden="true" />
                </a>
              </div>
            )}

            <p className="text-[11px] text-[var(--text-secondary)]">{t('disease.disclaimer')}</p>
          </div>
        </Card>
      )}
    </div>
  )
}
