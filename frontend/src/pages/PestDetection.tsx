import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Bug, Upload, ImageUp, ExternalLink } from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { IconBadge } from '@/components/ui/IconBadge'
import type { AdvisoryResult, PestDetectionResult } from '@/lib/types'

const SEVERITY_TONE: Record<string, 'brand' | 'warning' | 'critical' | 'neutral'> = {
  LOW: 'brand',
  MODERATE: 'warning',
  HIGH: 'critical',
  NONE: 'neutral',
}

const PRIORITY_TONE: Record<string, 'brand' | 'warning' | 'critical' | 'neutral'> = {
  LOW: 'neutral',
  MODERATE: 'warning',
  HIGH: 'critical',
}

export default function PestDetection() {
  const { t } = useTranslation()
  const { farm } = useAuth()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [annotated, setAnnotated] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<PestDetectionResult | null>(null)
  const [advisory, setAdvisory] = useState<AdvisoryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview)
    if (annotated) URL.revokeObjectURL(annotated)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function pickFile(f: File | null) {
    setResult(null)
    setAdvisory(null)
    setError('')
    setFile(f)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(f ? URL.createObjectURL(f) : null)
    if (annotated) URL.revokeObjectURL(annotated)
    setAnnotated(null)
  }

  async function analyze() {
    if (!file) return
    setLoading(true)
    setError('')
    setResult(null)
    setAdvisory(null)
    try {
      const form = new FormData()
      form.append('image', file)
      const { data } = await api.post<PestDetectionResult>('/api/pest/detect', form)
      setResult(data)

      if (data.status === 'detections_found') {
        const annotatedForm = new FormData()
        annotatedForm.append('image', file)
        api
          .post('/api/pest/detect/annotated', annotatedForm, { responseType: 'blob' })
          .then(({ data: blob }) => setAnnotated(URL.createObjectURL(blob as Blob)))
          .catch(() => {})

        api
          .post<AdvisoryResult>('/api/advisory/analyze', { crop: farm?.crop_type, pest_result: data })
          .then(({ data: adv }) => setAdvisory(adv))
          .catch(() => {})
      }
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const displayImage = annotated ?? preview

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('pest.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('pest.subtitle')}</p>
      </div>

      <Card>
        <CardHeader title={t('pest.upload_title')} action={<IconBadge icon={<Bug size={16} aria-hidden="true" />} tone="brand" />} />
        <div className="space-y-4 px-5 pb-5 pt-3">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/bmp"
            className="hidden"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />

          {displayImage ? (
            <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)]">
              <img src={displayImage} alt={t('pest.upload_title')} className="max-h-80 w-full object-contain bg-[var(--bg-surface-muted)]" />
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-[var(--border-subtle)] py-10 text-[var(--text-secondary)] transition-colors hover:border-brand-300 hover:text-brand-700"
            >
              <ImageUp size={28} aria-hidden="true" />
              <span className="text-sm font-medium">{t('pest.choose_photo')}</span>
              <span className="text-xs">{t('pest.upload_hint')}</span>
            </button>
          )}

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
              <Upload size={14} aria-hidden="true" /> {preview ? t('pest.choose_different') : t('pest.choose_photo')}
            </Button>
            <Button type="button" size="sm" onClick={analyze} disabled={!file} isLoading={loading}>
              {t('pest.analyze')}
            </Button>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>
      </Card>

      {result && (
        <Card>
          <CardHeader
            title={t('pest.result_title')}
            action={
              result.severity && result.status === 'detections_found' ? (
                <Badge tone={SEVERITY_TONE[result.severity.level]} dot>{t(`pest.severity_${result.severity.level.toLowerCase()}`)}</Badge>
              ) : undefined
            }
          />
          <div className="space-y-4 px-5 pb-5 pt-3">
            {result.status === 'detections_found' ? (
              <>
                <div>
                  <p className="text-lg font-bold text-[var(--text-primary)]">
                    {result.summary.total_pests} {t('pest.pests_found')} &middot; {result.summary.species_count} {t('pest.species_count')}
                  </p>
                  {result.message && <p className="mt-1 text-xs text-gold-600">{result.message}</p>}
                </div>

                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{t('pest.species_detected')}</p>
                  <div className="space-y-2">
                    {result.species.map((s) => (
                      <div key={s.name} className="flex items-center gap-3 text-sm">
                        <span className="w-40 shrink-0 truncate capitalize text-[var(--text-primary)]">{s.name}</span>
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--bg-surface-muted)]">
                          <div className="h-full rounded-full bg-brand-500" style={{ width: `${s.average_confidence * 100}%` }} />
                        </div>
                        <span className="w-24 shrink-0 text-right text-xs text-[var(--text-secondary)]">
                          &times;{s.count} &middot; {(s.average_confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="text-sm text-[var(--text-secondary)]">
                {result.status === 'no_pest_detected' ? t('pest.no_pest_detected') : t('pest.invalid_image')}
              </p>
            )}

            <p className="text-[11px] text-[var(--text-secondary)]">{t('pest.disclaimer')}</p>
          </div>
        </Card>
      )}

      {advisory && advisory.status === 'advisory_available' && (
        <Card>
          <CardHeader title={t('pest.advisory_title')} action={<IconBadge icon={<Bug size={16} aria-hidden="true" />} tone="amber" />} />
          <div className="space-y-4 px-5 pb-5 pt-3">
            {advisory.risk_assessments.map((r, i) => (
              <div key={i} className="rounded-xl bg-[var(--bg-surface-muted)] p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-[var(--text-primary)]">{r.category.replace(/_/g, ' ')}</span>
                  <Badge tone={PRIORITY_TONE[r.level] ?? 'neutral'}>{r.level}</Badge>
                </div>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">{r.note}</p>
              </div>
            ))}

            {advisory.recommendations.length > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{t('pest.recommendations')}</p>
                {advisory.recommendations.map((rec) => (
                  <div key={rec.rule_id} className="rounded-xl border border-[var(--border-subtle)] p-3">
                    <div className="flex items-center gap-2">
                      <Badge tone={PRIORITY_TONE[rec.priority] ?? 'neutral'}>{rec.priority}</Badge>
                      <span className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{rec.type.replace(/_/g, ' ')}</span>
                    </div>
                    <p className="mt-1.5 text-sm text-[var(--text-primary)]">{rec.action}</p>
                  </div>
                ))}
              </div>
            )}

            {advisory.sources.length > 0 && (
              <div className="flex flex-wrap gap-3">
                {advisory.sources.map((s) => (
                  <a
                    key={s.id}
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline"
                  >
                    {s.organization} <ExternalLink size={12} aria-hidden="true" />
                  </a>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
