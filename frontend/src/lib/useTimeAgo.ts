import { useTranslation } from 'react-i18next'

// Coarse "how long ago" for a live hardware heartbeat — recomputed on every
// render, which is frequent enough here since these pages re-render on every
// WebSocket sensor_update (~4s ticks) without needing a dedicated timer.
export function useTimeAgo(isoTimestamp: string | null | undefined): string | null {
  const { t } = useTranslation()
  if (!isoTimestamp) return null
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(isoTimestamp).getTime()) / 1000))
  if (seconds < 5) return t('common.just_now')
  if (seconds < 60) return t('common.seconds_ago', { count: seconds })
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return t('common.minutes_ago', { count: minutes })
  const hours = Math.floor(minutes / 60)
  return t('common.hours_ago', { count: hours })
}
