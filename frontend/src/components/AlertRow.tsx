import { useTranslation } from 'react-i18next'
import { AlertTriangle, Info, XCircle } from 'lucide-react'
import clsx from 'clsx'
import type { AlertItem } from '@/lib/types'

const severityIcon = { info: Info, warning: AlertTriangle, critical: XCircle }
const severityColor = {
  info: 'text-water-600 bg-water-50',
  warning: 'text-amber-600 bg-amber-50',
  critical: 'text-red-600 bg-red-50',
}

export function AlertRow({ alert }: { alert: AlertItem }) {
  const { t, i18n } = useTranslation()
  const Icon = severityIcon[alert.severity] ?? Info

  const time = new Date(alert.created_at).toLocaleTimeString(i18n.language, {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className={clsx('flex items-start gap-3 rounded-xl px-3 py-2.5 transition-colors', !alert.is_read && 'bg-[var(--bg-surface-muted)]')}>
      <span className={clsx('mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg', severityColor[alert.severity])} aria-hidden="true">
        <Icon size={14} aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-[var(--text-primary)]">{t(`alert_codes.${alert.code}`, alert.code)}</p>
        <p className="text-xs text-[var(--text-secondary)]">{time}</p>
      </div>
      {!alert.is_read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-500" aria-hidden="true" />}
    </div>
  )
}
