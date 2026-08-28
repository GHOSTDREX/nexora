import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import clsx from 'clsx'
import { Sprout, FlaskConical, Thermometer, Droplet, CloudRain, Wind } from 'lucide-react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { IconBadge } from '@/components/ui/IconBadge'
import { pageTransition, pageTransitionReduced } from '@/lib/motion'
import type { SensorReading } from '@/lib/types'

type Tab = 'soil' | 'npk' | 'environment'

const axisTick = { fill: 'var(--text-secondary)', fontSize: 11 }
const gridStroke = 'var(--chart-grid)'
const tooltipContentStyle = {
  background: 'var(--bg-surface)',
  border: '1px solid var(--border-subtle)',
  borderRadius: 10,
  color: 'var(--text-primary)',
  fontSize: 12,
}
const tooltipLabelStyle = { color: 'var(--text-secondary)' }

export default function MonitoringPage() {
  const { t, i18n } = useTranslation()
  const reduceMotion = useReducedMotion()
  const [tab, setTab] = useState<Tab>('soil')
  const [history, setHistory] = useState<SensorReading[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .get('/api/sensors/history?limit=60')
      .then(({ data }) => setHistory(data.history))
      .finally(() => setLoading(false))
  }, [])

  const chartData = useMemo(
    () =>
      history.map((r) => ({
        time: new Date(r.timestamp).toLocaleTimeString(i18n.language, { hour: '2-digit', minute: '2-digit' }),
        soil_moisture: r.soil_moisture,
        temperature: r.temperature,
        humidity: r.humidity,
        rainfall: r.rainfall,
        wind_speed: r.wind_speed,
        nitrogen: r.nitrogen,
        phosphorus: r.phosphorus,
        potassium: r.potassium,
      })),
    [history, i18n.language],
  )

  const tabs: { key: Tab; label: string }[] = [
    { key: 'soil', label: t('sensors.soil_moisture') },
    { key: 'npk', label: 'NPK' },
    { key: 'environment', label: t('sensors.environment') },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('nav.farm_monitoring')}</h1>

      <div className="inline-flex rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-1">
        {tabs.map((tb) => (
          <button
            key={tb.key}
            onClick={() => setTab(tb.key)}
            className={clsx(
              'relative rounded-lg px-4 py-1.5 text-sm font-medium transition-colors',
              tab === tb.key ? 'text-brand-900' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
            )}
          >
            {tab === tb.key && (
              <motion.span
                layoutId="monitoring-tab-pill"
                className="absolute inset-0 rounded-lg bg-brand-500"
                transition={{ type: 'spring', stiffness: 380, damping: 32 }}
              />
            )}
            <span className="relative z-10">{tb.label}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <Skeleton className="h-80 w-full" />
      ) : (
        <AnimatePresence mode="wait">
          <motion.div key={tab} variants={reduceMotion ? pageTransitionReduced : pageTransition} initial="initial" animate="animate" exit="exit">
          {tab === 'soil' && (
            <Card>
              <CardHeader title={t('sensors.soil_moisture')} subtitle="%" action={<IconBadge icon={<Sprout size={16} aria-hidden="true" />} tone="brand" />} />
              <div className="h-72 px-3 pb-4 pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="soilGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#7be05b" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="#7be05b" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridStroke} />
                    <XAxis dataKey="time" tickLine={false} axisLine={false} tick={axisTick} />
                    <YAxis tickLine={false} axisLine={false} width={32} tick={axisTick} />
                    <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
                    <Area type="monotone" dataKey="soil_moisture" stroke="#7be05b" fill="url(#soilGradient)" strokeWidth={2} name={t('sensors.soil_moisture')} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          {tab === 'npk' && (
            <Card>
              <CardHeader title="Nitrogen · Phosphorus · Potassium" subtitle="mg/kg" action={<IconBadge icon={<FlaskConical size={16} aria-hidden="true" />} tone="amber" />} />
              <div className="h-72 px-3 pb-4 pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData.slice(-20)}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridStroke} />
                    <XAxis dataKey="time" tickLine={false} axisLine={false} tick={axisTick} />
                    <YAxis tickLine={false} axisLine={false} width={32} tick={axisTick} />
                    <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#93a99b' }} />
                    <Bar dataKey="nitrogen" name={t('sensors.nitrogen')} fill="#7be05b" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="phosphorus" name={t('sensors.phosphorus')} fill="#f6c85f" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="potassium" name={t('sensors.potassium')} fill="#62b6ff" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          {tab === 'environment' && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader title={t('sensors.temperature')} subtitle="°C" action={<IconBadge icon={<Thermometer size={16} aria-hidden="true" />} tone="gold" />} />
                <div className="h-64 px-3 pb-4 pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f6c85f" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#f6c85f" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridStroke} />
                      <XAxis dataKey="time" tickLine={false} axisLine={false} tick={axisTick} />
                      <YAxis tickLine={false} axisLine={false} width={32} tick={axisTick} />
                      <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
                      <Area type="monotone" dataKey="temperature" stroke="#f6c85f" fill="url(#tempGradient)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              <Card>
                <CardHeader title={t('sensors.humidity')} subtitle="%" action={<IconBadge icon={<Droplet size={16} aria-hidden="true" />} tone="water" />} />
                <div className="h-64 px-3 pb-4 pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="humGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#62b6ff" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#62b6ff" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridStroke} />
                      <XAxis dataKey="time" tickLine={false} axisLine={false} tick={axisTick} />
                      <YAxis tickLine={false} axisLine={false} width={32} tick={axisTick} />
                      <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
                      <Area type="monotone" dataKey="humidity" stroke="#62b6ff" fill="url(#humGradient)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              <Card>
                <CardHeader title={t('sensors.rainfall')} subtitle="mm" action={<IconBadge icon={<CloudRain size={16} aria-hidden="true" />} tone="water" />} />
                <div className="h-64 px-3 pb-4 pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridStroke} />
                      <XAxis dataKey="time" tickLine={false} axisLine={false} tick={axisTick} />
                      <YAxis tickLine={false} axisLine={false} width={32} tick={axisTick} />
                      <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
                      <Bar dataKey="rainfall" fill="#5de2d0" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              <Card>
                <CardHeader title={t('sensors.wind_speed')} subtitle="km/h" action={<IconBadge icon={<Wind size={16} aria-hidden="true" />} tone="neutral" />} />
                <div className="h-64 px-3 pb-4 pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="windGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridStroke} />
                      <XAxis dataKey="time" tickLine={false} axisLine={false} tick={axisTick} />
                      <YAxis tickLine={false} axisLine={false} width={32} tick={axisTick} />
                      <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} />
                      <Area type="monotone" dataKey="wind_speed" stroke="#94a3b8" fill="url(#windGradient)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>
          )}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  )
}
