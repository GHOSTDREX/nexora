import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  Thermometer, Droplet, Sprout, FlaskConical, CloudRain, Sun, Cloud, CloudSnow, CloudLightning,
  Bot, Wheat, Camera, ArrowRight, Wind, Bell, HeartPulse, Clock,
} from 'lucide-react'
import { api, apiErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import { useFarmData } from '@/context/FarmDataContext'
import { StatCard } from '@/components/StatCard'
import { ManualSensorForm } from '@/components/ManualSensorForm'
import { Card, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { AlertRow } from '@/components/AlertRow'
import { Skeleton } from '@/components/ui/Skeleton'
import { IconBadge } from '@/components/ui/IconBadge'
import { staggerContainer } from '@/lib/motion'
import { useTimeAgo } from '@/lib/useTimeAgo'
import type { AlertItem, CropRecommendation, Farm, RobotStatus, SoilHealth, WeatherToday } from '@/lib/types'

function weatherVisual(condition?: string) {
  const c = condition ?? ''
  if (c.includes('thunder')) return { Icon: CloudLightning, tint: 'text-indigo-500', gradient: 'from-indigo-50' }
  if (c.includes('snow')) return { Icon: CloudSnow, tint: 'text-water-400', gradient: 'from-water-50' }
  if (c.includes('rain') || c.includes('drizzle') || c.includes('shower')) {
    return { Icon: CloudRain, tint: 'text-water-600', gradient: 'from-water-50' }
  }
  if (c.includes('fog') || c.includes('overcast') || c.includes('cloud')) {
    return { Icon: Cloud, tint: 'text-slate-400', gradient: 'from-slate-800' }
  }
  return { Icon: Sun, tint: 'text-gold-500', gradient: 'from-gold-50' }
}

export default function Dashboard() {
  const { t } = useTranslation()
  const { user, farm, setFarm } = useAuth()
  const { latestReading, robotLive, liveAlerts } = useFarmData()

  const [weather, setWeather] = useState<WeatherToday | null>(null)
  const [robot, setRobot] = useState<RobotStatus | null>(null)
  const [cropRec, setCropRec] = useState<CropRecommendation | null>(null)
  const [soilHealth, setSoilHealth] = useState<SoilHealth | null>(null)
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [cameraFrame, setCameraFrame] = useState<string | null>(null)
  const [streamUrl, setStreamUrl] = useState<string | null>(null)
  const [switchingSensorMode, setSwitchingSensorMode] = useState(false)
  const [sensorModeError, setSensorModeError] = useState('')

  useEffect(() => {
    api.get<WeatherToday>('/api/weather/today').then(({ data }) => setWeather(data)).catch(() => {})
    api.get<RobotStatus>('/api/robot/status').then(({ data }) => setRobot(data)).catch(() => {})
    api.get<CropRecommendation>('/api/crop/recommend/latest').then(({ data }) => setCropRec(data)).catch(() => {})
    api.get<SoilHealth>('/api/soil-health/latest').then(({ data }) => setSoilHealth(data)).catch(() => {})
    api.get<AlertItem[]>('/api/alerts?limit=5').then(({ data }) => setAlerts(data)).catch(() => {})

    function loadFrame() {
      api.get('/api/camera/frame').then(({ data }) => {
        setCameraFrame(data.image_data_url)
        setStreamUrl(data.stream_url ?? null)
      }).catch(() => {})
    }
    loadFrame()
    const interval = setInterval(loadFrame, 6000)
    return () => clearInterval(interval)
  }, [])

  const mergedAlerts = [...liveAlerts.filter((a) => a.id < 0), ...alerts].slice(0, 5)

  async function toggleSensorMode() {
    if (!farm) return
    setSwitchingSensorMode(true)
    setSensorModeError('')
    try {
      const nextMode = farm.sensor_mode === 'Manual' ? 'Auto' : 'Manual'
      const { data } = await api.patch<Farm>('/api/farm/sensor-mode', { sensor_mode: nextMode })
      setFarm(data)
    } catch (err) {
      setSensorModeError(apiErrorMessage(err))
    } finally {
      setSwitchingSensorMode(false)
    }
  }

  const pumpOn = robotLive?.pump_on ?? robot?.pump_on ?? false
  const robotConnected = robotLive?.robot_connected ?? robot?.robot_connected ?? true
  const lastSeen = useTimeAgo(latestReading?.timestamp)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">
          {t('dashboard.greeting', { name: user?.full_name?.split(' ')[0] ?? '' })}
        </h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">
          {t('dashboard.subtitle', { farm: farm?.name ?? '' })}
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-[var(--text-secondary)]">{t('sensors.environment')}</h2>
        <div className="flex items-center gap-2">
          <Badge tone={farm?.sensor_mode === 'Manual' ? 'neutral' : 'brand'}>
            {farm?.sensor_mode === 'Manual' ? t('common.manual') : t('common.auto')}
          </Badge>
          <Button variant="secondary" size="sm" onClick={toggleSensorMode} isLoading={switchingSensorMode}>
            {farm?.sensor_mode === 'Manual' ? t('dashboard.set_auto_mode') : t('dashboard.set_manual_mode')}
          </Button>
        </div>
      </div>

      {sensorModeError && <p className="text-sm text-red-400">{sensorModeError}</p>}

      {farm?.sensor_mode === 'Manual' && (
        <p className="rounded-xl bg-gold-50 px-4 py-2.5 text-sm text-gold-700">{t('dashboard.manual_sensor_hint')}</p>
      )}

      {farm?.sensor_mode === 'Manual' ? (
        <ManualSensorForm initial={latestReading} />
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4"
        >
          <StatCard icon={<Thermometer size={18} aria-hidden="true" />} label={t('sensors.temperature')} value="—" numericValue={latestReading?.temperature} decimals={1} unit="°C" tone="gold" live />
          <StatCard icon={<Droplet size={18} aria-hidden="true" />} label={t('sensors.humidity')} value="—" numericValue={latestReading?.humidity} unit="%" tone="water" live />
          <StatCard icon={<Sprout size={18} aria-hidden="true" />} label={t('sensors.soil_moisture')} value="—" numericValue={latestReading?.soil_moisture} unit="%" tone="brand" live />
          <StatCard icon={<FlaskConical size={18} aria-hidden="true" />} label={t('sensors.nitrogen')} value="—" numericValue={latestReading?.nitrogen} unit="mg/kg" tone="amber" live />
          <StatCard icon={<FlaskConical size={18} aria-hidden="true" />} label={t('sensors.phosphorus')} value="—" numericValue={latestReading?.phosphorus} unit="mg/kg" tone="gold" live />
          <StatCard icon={<FlaskConical size={18} aria-hidden="true" />} label={t('sensors.potassium')} value="—" numericValue={latestReading?.potassium} unit="mg/kg" tone="brand" live />
          <StatCard icon={<CloudRain size={18} aria-hidden="true" />} label={t('sensors.rain_status')} value={latestReading?.rain_detected ? t('sensors.rain_detected') : t('sensors.no_rain')} tone="water" live />
          <StatCard icon={<Clock size={18} aria-hidden="true" />} label={t('sensors.last_updated')} value={lastSeen ?? '—'} tone="neutral" live />
        </motion.div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card interactive className="lg:col-span-1">
          <CardHeader title={t('dashboard.todays_weather')} action={<IconBadge icon={<Sun size={16} aria-hidden="true" />} tone="gold" />} />
          <div className="px-5 pb-5 pt-3">
            {weather ? (
              (() => {
                const { Icon, tint, gradient } = weatherVisual(weather.condition)
                return (
                  <div>
                    <div className={`flex items-center gap-4 rounded-2xl bg-gradient-to-br ${gradient} to-transparent p-4`}>
                      <Icon size={38} className={tint} aria-hidden="true" />
                      <p className="font-heading text-3xl font-bold text-[var(--text-primary)]">{weather.temperature_c}°C</p>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                      <div>
                        <CloudRain size={14} className="mx-auto text-water-500" aria-hidden="true" />
                        <p className="mt-1 text-sm font-semibold text-[var(--text-primary)]">{weather.rain_probability_pct}%</p>
                        <p className="text-[11px] text-[var(--text-secondary)]">{t('dashboard.rain_probability')}</p>
                      </div>
                      <div>
                        <Droplet size={14} className="mx-auto text-water-500" aria-hidden="true" />
                        <p className="mt-1 text-sm font-semibold text-[var(--text-primary)]">{weather.humidity_pct}%</p>
                        <p className="text-[11px] text-[var(--text-secondary)]">{t('sensors.humidity')}</p>
                      </div>
                      <div>
                        <Wind size={14} className="mx-auto text-slate-500" aria-hidden="true" />
                        <p className="mt-1 text-sm font-semibold text-[var(--text-primary)]">{weather.wind_speed_kmh}</p>
                        <p className="text-[11px] text-[var(--text-secondary)]">{t('dashboard.wind')}</p>
                      </div>
                    </div>
                  </div>
                )
              })()
            ) : (
              <Skeleton className="h-24 w-full" />
            )}
          </div>
        </Card>

        <Card interactive className="lg:col-span-1">
          <CardHeader title={t('dashboard.robot_status')} action={<IconBadge icon={<Bot size={16} aria-hidden="true" />} tone="amber" />} />
          <div className="space-y-2.5 px-5 pb-5 pt-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-[var(--text-secondary)]">{t('robot.status')}</span>
              <Badge tone={robotConnected ? 'brand' : 'critical'} dot>{robotConnected ? t('common.connected') : t('common.disconnected')}</Badge>
            </div>
            {lastSeen && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-[var(--text-secondary)]">{t('common.last_seen')}</span>
                <span className="text-[var(--text-primary)]">{lastSeen}</span>
              </div>
            )}
            <div className="flex items-center justify-between text-sm">
              <span className="text-[var(--text-secondary)]">{t('robot.control')}: {t('irrigation.pump')}</span>
              <Badge tone={pumpOn ? 'brand' : 'neutral'}>{pumpOn ? t('common.on') : t('common.off')}</Badge>
            </div>
            <Link to="/robot" className="mt-1 flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline">
              {t('common.view_all')} <ArrowRight size={12} aria-hidden="true" />
            </Link>
          </div>
        </Card>

        <Card interactive className="lg:col-span-1">
          <CardHeader title={t('dashboard.camera_preview')} action={<IconBadge icon={<Camera size={16} aria-hidden="true" />} tone="amber" />} />
          <div className="px-5 pb-5 pt-3">
            {streamUrl ? (
              <img src={streamUrl} alt="Camera feed" className="aspect-video w-full rounded-xl object-cover" />
            ) : cameraFrame ? (
              <img src={cameraFrame} alt="Camera feed" className="aspect-video w-full rounded-xl object-cover" />
            ) : (
              <Skeleton className="aspect-video w-full" />
            )}
            <Link to="/robot" className="mt-3 flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline">
              {t('common.view_all')} <ArrowRight size={12} aria-hidden="true" />
            </Link>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
        <Card interactive className="lg:col-span-1">
          <CardHeader title={t('dashboard.current_recommendation')} action={<IconBadge icon={<Wheat size={16} aria-hidden="true" />} tone="gold" />} />
          <div className="px-5 pb-5 pt-3">
            {cropRec ? (
              <div>
                <p className="text-xl font-bold capitalize text-[var(--text-primary)]">{cropRec.top_crop}</p>
                <p className="text-sm text-[var(--text-secondary)]">{t('crop.model_confidence')}: {cropRec.confidence}%</p>
              </div>
            ) : (
              <Skeleton className="h-6 w-24" />
            )}
            <Link to="/crop-recommendation" className="mt-3 flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline">
              {t('common.view_all')} <ArrowRight size={12} aria-hidden="true" />
            </Link>
          </div>
        </Card>

        <Card interactive className="lg:col-span-1">
          <CardHeader title={t('soil_health.title')} action={<IconBadge icon={<HeartPulse size={16} aria-hidden="true" />} tone="brand" />} />
          <div className="px-5 pb-5 pt-3">
            {soilHealth ? (
              <div>
                <p className="text-xl font-bold text-[var(--text-primary)]">{soilHealth.health_score}<span className="ml-1 text-sm font-medium text-[var(--text-secondary)]">/ 100</span></p>
                <Badge tone={soilHealth.overall_status === 'Healthy' ? 'brand' : soilHealth.overall_status === 'High Stress' ? 'critical' : 'warning'}>
                  {t(`soil_health.status_${soilHealth.overall_status.toLowerCase().replace(/ /g, '_')}`, soilHealth.overall_status)}
                </Badge>
              </div>
            ) : (
              <Skeleton className="h-6 w-24" />
            )}
            <Link to="/soil-health" className="mt-3 flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline">
              {t('common.view_all')} <ArrowRight size={12} aria-hidden="true" />
            </Link>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title={t('dashboard.recent_alerts')} action={<IconBadge icon={<Bell size={16} aria-hidden="true" />} tone="amber" />} />
          <div className="space-y-1 px-3 pb-4 pt-2">
            {mergedAlerts.length === 0 ? (
              <p className="px-2 py-4 text-sm text-[var(--text-secondary)]">{t('dashboard.no_alerts')}</p>
            ) : (
              mergedAlerts.map((a) => <AlertRow key={a.id} alert={a} />)
            )}
            <Link to="/alerts" className="ml-2 mt-1 flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline">
              {t('common.view_all')} <ArrowRight size={12} aria-hidden="true" />
            </Link>
          </div>
        </Card>
      </div>
    </div>
  )
}
