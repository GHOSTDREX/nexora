import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Landmark, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { IconBadge } from '@/components/ui/IconBadge'
import { Skeleton } from '@/components/ui/Skeleton'
import type { SchemeMatchResponse } from '@/lib/types'

export default function Schemes() {
  const { t, i18n } = useTranslation()
  const [schemes, setSchemes] = useState<SchemeMatchResponse | null>(null)

  useEffect(() => {
    api.get<SchemeMatchResponse>('/api/schemes/match', { params: { language: i18n.language } })
      .then(({ data }) => setSchemes(data))
      .catch(() => {})
  }, [i18n.language])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('nav.schemes')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('dashboard.schemes_title')}</p>
      </div>

      <Card>
        <CardHeader title={t('dashboard.schemes_title')} action={<IconBadge icon={<Landmark size={16} aria-hidden="true" />} tone="brand" />} />
        <div className="px-5 pb-5 pt-3">
          {!schemes ? (
            <Skeleton className="h-24 w-full" />
          ) : schemes.schemes.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">{t('dashboard.schemes_no_match')}</p>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {schemes.schemes.map((s) => (
                  <a
                    key={s.id}
                    href={s.link}
                    target="_blank"
                    rel="noreferrer"
                    className="group rounded-xl border border-[var(--border-subtle)] p-3 transition-colors hover:bg-[var(--bg-surface-muted)]"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-[var(--text-primary)]">{s.name}</p>
                      <ExternalLink size={13} className="mt-0.5 shrink-0 text-[var(--text-secondary)] group-hover:text-brand-700" aria-hidden="true" />
                    </div>
                    <p className="mt-1 text-xs text-[var(--text-secondary)]">{s.description}</p>
                  </a>
                ))}
              </div>
              <p className="mt-3 text-[11px] text-[var(--text-secondary)]">{schemes.disclaimer}</p>
            </>
          )}
        </div>
      </Card>
    </div>
  )
}
