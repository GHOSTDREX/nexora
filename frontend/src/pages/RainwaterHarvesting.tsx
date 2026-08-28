import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { CloudRain, DoorOpen, DoorClosed, Droplets } from 'lucide-react'
import { api } from '@/lib/api'
import { useFarmData } from '@/context/FarmDataContext'
import { Card, CardHeader } from '@/components/ui/Card'
import { IconBadge } from '@/components/ui/IconBadge'
import type { RobotActionLog, RobotStatus } from '@/lib/types'

export default function RainwaterHarvesting() {
  const { t, i18n } = useTranslation()
  const { latestReading, robotLive } = useFarmData()
  const [status, setStatus] = useState<RobotStatus | null>(null)
  const [actions, setActions] = useState<RobotActionLog[]>([])

  useEffect(() => {
    api.get<RobotStatus>('/api/robot/status').then(({ data }) => setStatus(data)).catch(() => {})
    api
      .get('/api/robot/actions?limit=50')
      .then(({ data }) => setActions(data.filter((a: RobotActionLog) => a.action_type.startsWith('lid'))))
      .catch(() => {})
  }, [])

  const lidOpen = robotLive?.lid_open ?? status?.lid_open ?? false
  const rainDetected = latestReading?.rain_detected ?? false

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('rainwater.title')}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('rainwater.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="flex flex-col items-center justify-center gap-3 p-8 text-center">
          <motion.div
            key={String(rainDetected)}
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`flex h-16 w-16 items-center justify-center rounded-2xl shadow-sm ${rainDetected ? 'bg-water-400 text-brand-900 shadow-black/30' : 'bg-slate-700 text-slate-300'}`}
          >
            <CloudRain size={30} aria-hidden="true" />
          </motion.div>
          <p className="text-sm font-medium text-[var(--text-secondary)]">{t('rainwater.rain_sensor')}</p>
          <p className="text-lg font-bold text-[var(--text-primary)]">
            {rainDetected ? t('sensors.rain_detected') : t('sensors.no_rain')}
          </p>
        </Card>

        <Card className="flex flex-col items-center justify-center gap-3 p-8 text-center">
          <motion.div
            key={String(lidOpen)}
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`flex h-16 w-16 items-center justify-center rounded-2xl shadow-sm ${lidOpen ? 'bg-brand-500 text-brand-900 shadow-black/30' : 'bg-slate-700 text-slate-300'}`}
          >
            {lidOpen ? <DoorOpen size={30} aria-hidden="true" /> : <DoorClosed size={30} aria-hidden="true" />}
          </motion.div>
          <p className="text-sm font-medium text-[var(--text-secondary)]">{t('rainwater.lid_status')}</p>
          <p className="text-lg font-bold text-[var(--text-primary)]">{lidOpen ? t('common.open') : t('common.closed')}</p>
        </Card>
      </div>

      <Card>
        <CardHeader title={t('robot.title')} action={<IconBadge icon={<Droplets size={16} aria-hidden="true" />} tone="water" />} />
        <div className="space-y-1 px-5 pb-5 pt-3">
          {actions.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">—</p>
          ) : (
            actions.map((a, i) => (
              <div key={i} className="flex items-center justify-between border-b border-[var(--border-subtle)] py-2 text-sm last:border-0">
                <span className="text-[var(--text-primary)]">{t(`robot.${a.action_type}`, a.action_type)}</span>
                <span className="text-xs text-[var(--text-secondary)]">
                  {new Date(a.timestamp).toLocaleString(i18n.language)}
                </span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
