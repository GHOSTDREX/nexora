import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCheck } from 'lucide-react'
import { api } from '@/lib/api'
import { useFarmData } from '@/context/FarmDataContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { AlertRow } from '@/components/AlertRow'
import { staggerContainer, staggerItem } from '@/lib/motion'
import type { AlertItem } from '@/lib/types'

export default function Alerts() {
  const { t } = useTranslation()
  const { clearUnread } = useFarmData()
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api
      .get<AlertItem[]>(`/api/alerts?limit=100${unreadOnly ? '&unread_only=true' : ''}`)
      .then(({ data }) => setAlerts(data))
      .finally(() => setLoading(false))
  }

  useEffect(load, [unreadOnly])

  async function markAllRead() {
    await api.post('/api/alerts/read-all')
    clearUnread()
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('alerts_page.title')}</h1>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-sm text-[var(--text-secondary)]">
            <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
            {t('alerts_page.unread_only')}
          </label>
          <Button variant="secondary" size="sm" onClick={markAllRead}>
            <CheckCheck size={14} aria-hidden="true" /> {t('alerts_page.mark_all_read')}
          </Button>
        </div>
      </div>

      <Card>
        {loading ? (
          <p className="px-5 py-4 text-sm text-[var(--text-secondary)]">{t('common.loading')}</p>
        ) : alerts.length === 0 ? (
          <p className="px-5 py-4 text-sm text-[var(--text-secondary)]">{t('alerts_page.no_alerts')}</p>
        ) : (
          <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-1 px-3 py-3">
            <AnimatePresence>
              {alerts.map((a) => (
                <motion.div key={a.id} variants={staggerItem} exit={{ opacity: 0, height: 0 }} layout>
                  <AlertRow alert={a} />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </Card>
    </div>
  )
}
