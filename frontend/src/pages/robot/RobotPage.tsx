import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Square, Camera as CameraIcon,
  Sprout, Power, PowerOff, ArrowDownToLine, ArrowUpFromLine,
  RotateCcw, RotateCw, ChevronUp, ChevronDown, Crosshair, Battery, Bot, Images,
} from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import { useFarmData } from '@/context/FarmDataContext'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { IconBadge } from '@/components/ui/IconBadge'
import { staggerContainer, staggerItem } from '@/lib/motion'
import { useTimeAgo } from '@/lib/useTimeAgo'
import type { CameraSnapshot, RobotStatus } from '@/lib/types'

export default function RobotPage() {
  const { t } = useTranslation()
  const { farm } = useAuth()
  const { robotLive, latestReading } = useFarmData()

  const [status, setStatus] = useState<RobotStatus | null>(null)
  const [cameraFrame, setCameraFrame] = useState<string | null>(null)
  const [streamUrl, setStreamUrl] = useState<string | null>(null)
  const [snapshots, setSnapshots] = useState<CameraSnapshot[]>([])
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [speed, setSpeed] = useState(100)
  const speedDebounce = useRef<ReturnType<typeof setTimeout> | null>(null)

  const loadStatus = useCallback(() => {
    api.get<RobotStatus>('/api/robot/status').then(({ data }) => setStatus(data)).catch(() => {})
  }, [])

  const loadFrame = useCallback(() => {
    api.get('/api/camera/frame').then(({ data }) => {
      setCameraFrame(data.image_data_url)
      setStreamUrl(data.stream_url ?? null)
    }).catch(() => {})
  }, [])

  const loadSnapshots = useCallback(() => {
    api.get<CameraSnapshot[]>('/api/camera/snapshots').then(({ data }) => setSnapshots(data)).catch(() => {})
  }, [])

  useEffect(() => {
    loadStatus()
    loadFrame()
    loadSnapshots()
    const interval = setInterval(loadFrame, 5000)
    return () => clearInterval(interval)
  }, [loadStatus, loadFrame, loadSnapshots])

  useEffect(() => {
    if (status?.motor_speed != null) setSpeed(status.motor_speed)
  }, [status?.motor_speed])

  useEffect(() => () => {
    if (speedDebounce.current) clearTimeout(speedDebounce.current)
  }, [])

  function onSpeedChange(value: number) {
    setSpeed(value)
    if (speedDebounce.current) clearTimeout(speedDebounce.current)
    speedDebounce.current = setTimeout(() => {
      api.post('/api/robot/action', { action_type: 'set_speed', value }).catch(() => {})
    }, 250)
  }

  async function doAction(action_type: string) {
    setError('')
    setBusy(action_type)
    try {
      await api.post('/api/robot/action', { action_type })
      loadStatus()
    } catch (err) {
      setError(apiErrorMessage(err, t('common.error_generic')))
    } finally {
      setBusy(null)
    }
  }

  async function doMove(direction: string) {
    setError('')
    setBusy(direction)
    try {
      const { data } = await api.post('/api/camera/move', { direction })
      setCameraFrame(data.image_data_url)
    } catch (err) {
      setError(apiErrorMessage(err, t('common.error_generic')))
    } finally {
      setBusy(null)
    }
  }

  async function doCapture() {
    setError('')
    setBusy('capture')
    try {
      await api.post('/api/camera/capture')
      loadSnapshots()
    } catch (err) {
      setError(apiErrorMessage(err, t('common.error_generic')))
    } finally {
      setBusy(null)
    }
  }

  const pumpOn = robotLive?.pump_on ?? status?.pump_on ?? false
  const connected = robotLive?.robot_connected ?? status?.robot_connected ?? true
  const isManual = farm?.irrigation_mode === 'Manual' || farm?.sensor_mode === 'Manual'
  const lastSeen = useTimeAgo(latestReading?.timestamp)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('robot.title')}</h1>
      </div>

      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <motion.div variants={staggerItem}>
          <Card interactive className="flex items-center gap-3 p-4">
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${connected ? 'bg-brand-500 live-pulse' : 'bg-red-500'}`} aria-hidden="true" />
            <div>
              <p className="text-xs text-[var(--text-secondary)]">{t('robot.status')}</p>
              <p className="text-sm font-semibold text-[var(--text-primary)]">{connected ? t('common.connected') : t('common.disconnected')}</p>
              {lastSeen && <p className="text-[11px] text-[var(--text-secondary)]">{t('common.last_seen')}: {lastSeen}</p>}
            </div>
          </Card>
        </motion.div>
        <motion.div variants={staggerItem}>
          <Card interactive className="flex items-center gap-3 p-4">
            <IconBadge icon={<Battery size={18} aria-hidden="true" />} tone="brand" />
            <div>
              <p className="text-xs text-[var(--text-secondary)]">{t('robot.battery')}</p>
              <p className="text-sm font-semibold text-[var(--text-primary)]">{status?.robot_battery_pct?.toFixed(0) ?? '—'}%</p>
            </div>
          </Card>
        </motion.div>
        <motion.div variants={staggerItem}>
          <Card interactive className="flex items-center gap-3 p-4">
            <IconBadge icon={pumpOn ? <Power size={18} aria-hidden="true" /> : <PowerOff size={18} aria-hidden="true" />} tone={pumpOn ? 'brand' : 'neutral'} />
            <div>
              <p className="text-xs text-[var(--text-secondary)]">{t('irrigation.pump')}</p>
              <p className="text-sm font-semibold text-[var(--text-primary)]">{pumpOn ? t('common.on') : t('common.off')}</p>
            </div>
          </Card>
        </motion.div>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title={t('robot.camera')} action={<IconBadge icon={<CameraIcon size={16} aria-hidden="true" />} tone="amber" />} />
          <div className="px-5 pb-5 pt-3">
            {streamUrl ? (
              <img
                src={streamUrl}
                alt="Live camera feed of the field"
                className="aspect-video w-full rounded-xl object-cover"
              />
            ) : cameraFrame ? (
              <motion.img
                key={cameraFrame.slice(-24)}
                initial={{ opacity: 0.4 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.25 }}
                src={cameraFrame}
                alt="Live camera feed of the field"
                className="aspect-video w-full rounded-xl object-cover"
              />
            ) : (
              <Skeleton className="aspect-video w-full" />
            )}

            <p className="mb-2 mt-4 text-xs font-semibold text-[var(--text-secondary)]">{t('robot.camera_controller')}</p>
            <div className="flex items-center justify-center gap-2">
              <Button variant="secondary" size="sm" onClick={() => doMove('pan_left')} isLoading={busy === 'pan_left'}>
                <RotateCcw size={14} aria-hidden="true" /> {t('robot.pan_left')}
              </Button>
              <Button variant="secondary" size="icon" onClick={() => doMove('tilt_up')} isLoading={busy === 'tilt_up'} aria-label={t('robot.tilt_up')}>
                <ChevronUp size={16} aria-hidden="true" />
              </Button>
              <Button variant="secondary" size="sm" onClick={() => doMove('pan_right')} isLoading={busy === 'pan_right'}>
                {t('robot.pan_right')} <RotateCw size={14} aria-hidden="true" />
              </Button>
            </div>
            <div className="mt-2 flex items-center justify-center gap-2">
              <Button variant="secondary" size="sm" onClick={() => doMove('center')} isLoading={busy === 'center'}>
                <Crosshair size={14} aria-hidden="true" /> {t('robot.center')}
              </Button>
              <Button variant="secondary" size="icon" onClick={() => doMove('tilt_down')} isLoading={busy === 'tilt_down'} aria-label={t('robot.tilt_down')}>
                <ChevronDown size={16} aria-hidden="true" />
              </Button>
            </div>
            <Button className="mt-4 w-full" onClick={doCapture} isLoading={busy === 'capture'}>
              <CameraIcon size={15} aria-hidden="true" /> {t('robot.capture')}
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader title={t('robot.control')} action={<IconBadge icon={<Bot size={16} aria-hidden="true" />} tone="amber" />} />
          <div className="space-y-5 px-5 pb-5 pt-3">
            <div>
              <p className="mb-2 text-xs font-semibold text-[var(--text-secondary)]">{t('robot.title')} — {t('common.manual')}</p>
              <div className="rounded-2xl bg-[var(--bg-surface-muted)] py-4">
                <div className="mx-auto grid w-fit grid-cols-3 gap-2">
                  <span />
                  <Button variant="secondary" size="icon" onClick={() => doAction('move_forward')} isLoading={busy === 'move_forward'} aria-label={t('robot.move_forward')}>
                    <ArrowUp size={18} aria-hidden="true" />
                  </Button>
                  <span />
                  <Button variant="secondary" size="icon" onClick={() => doAction('move_left')} isLoading={busy === 'move_left'} aria-label={t('robot.move_left')}>
                    <ArrowLeft size={18} aria-hidden="true" />
                  </Button>
                  <Button variant="secondary" size="icon" onClick={() => doAction('move_stop')} isLoading={busy === 'move_stop'} aria-label={t('robot.move_stop')}>
                    <Square size={16} aria-hidden="true" />
                  </Button>
                  <Button variant="secondary" size="icon" onClick={() => doAction('move_right')} isLoading={busy === 'move_right'} aria-label={t('robot.move_right')}>
                    <ArrowRight size={18} aria-hidden="true" />
                  </Button>
                  <span />
                  <Button variant="secondary" size="icon" onClick={() => doAction('move_back')} isLoading={busy === 'move_back'} aria-label={t('robot.move_back')}>
                    <ArrowDown size={18} aria-hidden="true" />
                  </Button>
                  <span />
                </div>
              </div>
            </div>

            <div>
              <p className="mb-2 flex items-center justify-between text-xs font-semibold text-[var(--text-secondary)]">
                {t('robot.speed')}
                <span className="text-[var(--text-primary)]">{speed}</span>
              </p>
              <input
                type="range"
                min={0}
                max={255}
                value={speed}
                onChange={(e) => onSpeedChange(Number(e.target.value))}
                className="w-full accent-brand-600"
                aria-label={t('robot.speed')}
              />
            </div>

            <div>
              <p className="mb-2 flex items-center justify-between text-xs font-semibold text-[var(--text-secondary)]">
                {t('irrigation.pump')}
                {!isManual && <Badge tone="neutral">{t('robot.manual_required')}</Badge>}
              </p>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" disabled={!isManual} onClick={() => doAction('pump_on')} isLoading={busy === 'pump_on'}>
                  <Power size={14} aria-hidden="true" /> {t('robot.pump_on')}
                </Button>
                <Button variant="secondary" size="sm" disabled={!isManual} onClick={() => doAction('pump_off')} isLoading={busy === 'pump_off'}>
                  <PowerOff size={14} aria-hidden="true" /> {t('robot.pump_off')}
                </Button>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold text-[var(--text-secondary)]">{t('robot.seed_dispenser')}</p>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => doAction('seed_on')} isLoading={busy === 'seed_on'}>
                  <Sprout size={14} aria-hidden="true" /> {t('robot.seed_on')}
                </Button>
                <Button variant="secondary" size="sm" onClick={() => doAction('seed_off')} isLoading={busy === 'seed_off'}>
                  <Sprout size={14} aria-hidden="true" /> {t('robot.seed_off')}
                </Button>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold text-[var(--text-secondary)]">{t('robot.plow')}</p>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => doAction('plow_on')} isLoading={busy === 'plow_on'}>
                  <ArrowDownToLine size={14} aria-hidden="true" /> {t('robot.plow_on')}
                </Button>
                <Button variant="secondary" size="sm" onClick={() => doAction('plow_off')} isLoading={busy === 'plow_off'}>
                  <ArrowUpFromLine size={14} aria-hidden="true" /> {t('robot.plow_off')}
                </Button>
              </div>
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title={t('robot.snapshots')} action={<IconBadge icon={<Images size={16} aria-hidden="true" />} tone="amber" />} />
        <div className="px-5 pb-5 pt-3">
          {snapshots.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">{t('robot.no_snapshots')}</p>
          ) : (
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="show"
              className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4"
            >
              {snapshots.map((s) => (
                <motion.div
                  key={s.id}
                  variants={staggerItem}
                  whileHover={{ scale: 1.03 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden rounded-xl border border-[var(--border-subtle)]"
                >
                  <img src={s.image_data_url} alt={`Field snapshot captured ${new Date(s.timestamp).toLocaleString()}`} className="aspect-video w-full object-cover" />
                  <p className="px-2 py-1.5 text-[11px] text-[var(--text-secondary)]">
                    {new Date(s.timestamp).toLocaleString()}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </Card>
    </div>
  )
}
