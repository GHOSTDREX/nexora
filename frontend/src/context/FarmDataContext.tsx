import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '@/lib/api'
import { useFarmSocket, type FarmSocketMessage } from '@/hooks/useFarmSocket'
import { useAuth } from '@/context/AuthContext'
import type { AlertItem, SensorReading } from '@/lib/types'

interface RobotLive {
  pump_on: boolean
  robot_connected: boolean
}

interface FarmDataValue {
  latestReading: SensorReading | null
  robotLive: RobotLive | null
  liveAlerts: AlertItem[]
  unreadCount: number
  bumpUnread: () => void
  clearUnread: () => void
  refreshLatest: () => Promise<void>
}

const FarmDataContext = createContext<FarmDataValue | null>(null)

export function FarmDataProvider({ children }: { children: ReactNode }) {
  const { farm } = useAuth()
  const [latestReading, setLatestReading] = useState<SensorReading | null>(null)
  const [robotLive, setRobotLive] = useState<RobotLive | null>(null)
  const [liveAlerts, setLiveAlerts] = useState<AlertItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  const refreshLatest = useCallback(async () => {
    if (!farm) return
    try {
      const { data } = await api.get<SensorReading>('/api/sensors/latest')
      setLatestReading(data)
    } catch {
      // no reading yet
    }
  }, [farm])

  useEffect(() => {
    refreshLatest()
    if (farm) {
      api
        .get<AlertItem[]>('/api/alerts?limit=200&unread_only=true')
        .then(({ data }) => setUnreadCount(data.length))
        .catch(() => {})
    }
  }, [farm, refreshLatest])

  const onMessage = useCallback((msg: FarmSocketMessage) => {
    if (msg.type === 'sensor_update') {
      setLatestReading((prev) => ({
        ...(prev as SensorReading),
        id: (prev?.id ?? 0) + 1,
        device_id: prev?.device_id ?? 'ESP32_FIELD_01',
        status: 'LIVE',
        ...msg.reading,
      }) as SensorReading)
      setRobotLive(msg.robot)
      if (msg.alerts.length > 0) {
        const now = new Date().toISOString()
        setLiveAlerts((prev) => [
          ...msg.alerts.map((a, i) => ({
            id: -Date.now() - i,
            code: a.code,
            severity: a.severity as AlertItem['severity'],
            params: a.params,
            is_read: false,
            created_at: now,
          })),
          ...prev,
        ].slice(0, 20))
        setUnreadCount((c) => c + msg.alerts.length)
      }
    }
  }, [])

  useFarmSocket(onMessage, !!farm)

  return (
    <FarmDataContext.Provider
      value={{
        latestReading,
        robotLive,
        liveAlerts,
        unreadCount,
        bumpUnread: () => setUnreadCount((c) => c + 1),
        clearUnread: () => setUnreadCount(0),
        refreshLatest,
      }}
    >
      {children}
    </FarmDataContext.Provider>
  )
}

export function useFarmData() {
  const ctx = useContext(FarmDataContext)
  if (!ctx) throw new Error('useFarmData must be used within FarmDataProvider')
  return ctx
}
