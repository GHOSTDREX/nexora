import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Store, MapPin, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { IconBadge } from '@/components/ui/IconBadge'
import { Skeleton } from '@/components/ui/Skeleton'
import type { MarketOverview } from '@/lib/types'

export default function MarketPrice() {
  const { t } = useTranslation()
  const [market, setMarket] = useState<MarketOverview | null>(null)

  useEffect(() => {
    api.get<MarketOverview>('/api/market/overview').then(({ data }) => setMarket(data)).catch(() => {})
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('nav.market')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">
          {market ? t('dashboard.market_title', { crop: t(`options.crop_type.${market.crop}`, market.crop) }) : t('nav.market')}
        </p>
      </div>

      <Card>
        <CardHeader title={t('dashboard.market_title', { crop: market ? t(`options.crop_type.${market.crop}`, market.crop) : '' })} action={<IconBadge icon={<Store size={16} aria-hidden="true" />} tone="amber" />} />
        <div className="px-5 pb-5 pt-3">
          {!market ? (
            <Skeleton className="h-24 w-full" />
          ) : (
            <>
              {market.mandi.configured ? (
                market.mandi.prices.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs uppercase tracking-wide text-[var(--text-secondary)]">
                          <th className="py-1.5 pr-3 font-medium">{t('dashboard.market_market')}</th>
                          <th className="py-1.5 pr-3 font-medium">{t('dashboard.market_modal_price')}</th>
                          <th className="py-1.5 pr-3 font-medium">{t('dashboard.market_range')}</th>
                          <th className="py-1.5 font-medium">{t('dashboard.market_date')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {market.mandi.prices.map((p, i) => (
                          <tr key={i} className="border-t border-[var(--border-subtle)]">
                            <td className="py-1.5 pr-3 text-[var(--text-primary)]">{p.market ?? '—'}{p.district ? `, ${p.district}` : ''}</td>
                            <td className="py-1.5 pr-3 font-semibold text-[var(--text-primary)]">{p.modal_price != null ? `₹${p.modal_price}` : '—'}</td>
                            <td className="py-1.5 pr-3 text-[var(--text-secondary)]">{p.min_price != null && p.max_price != null ? `₹${p.min_price} – ₹${p.max_price}` : '—'}</td>
                            <td className="py-1.5 text-[var(--text-secondary)]">{p.arrival_date ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-[var(--text-secondary)]">{t('dashboard.market_no_data')}</p>
                )
              ) : (
                <p className="text-sm text-[var(--text-secondary)]">{t('dashboard.market_not_configured')}</p>
              )}

              <div className="mt-4 flex flex-wrap gap-2 border-t border-[var(--border-subtle)] pt-3.5">
                <a href={market.dealers.nearest_search_url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 rounded-lg bg-[var(--bg-surface-muted)] px-3 py-1.5 text-xs font-semibold text-[var(--text-primary)] hover:bg-brand-50">
                  <MapPin size={13} aria-hidden="true" /> {t('dashboard.market_find_dealer')}
                </a>
                <a href={market.dealers.kvk_portal_url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 rounded-lg bg-[var(--bg-surface-muted)] px-3 py-1.5 text-xs font-semibold text-[var(--text-primary)] hover:bg-brand-50">
                  <ExternalLink size={13} aria-hidden="true" /> {t('dashboard.market_kvk_portal')}
                </a>
              </div>
            </>
          )}
        </div>
      </Card>
    </div>
  )
}
