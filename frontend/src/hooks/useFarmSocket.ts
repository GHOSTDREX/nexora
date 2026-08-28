import { useEffect, useRef } from 'react'
import { WS_URL, getToken } from '@/lib/api'

export interface FarmSocketMessage {
  type: 'sensor_update'
  reading: Record<string, number | boolean | string>
  robot: { pump_on: boolean; lid_open: boolean; robot_connected: boolean }
  alerts: { code: string; severity: string; params: Record<string, unknown> }[]
}

export function useFarmSocket(onMessage: (msg: FarmSocketMessage) => void, enabled = true) {
  const handlerRef = useRef(onMessage)
  handlerRef.current = onMessage

  useEffect(() => {
    if (!enabled) return

    let socket: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let closedByEffect = false

    function connect() {
      const token = getToken()
      if (!token) return
      socket = new WebSocket(`${WS_URL}/ws/farm?token=${encodeURIComponent(token)}`)

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as FarmSocketMessage
          handlerRef.current(data)
        } catch {
          // ignore malformed frames
        }
      }

      socket.onclose = () => {
        if (!closedByEffect) {
          reconnectTimer = setTimeout(connect, 3000)
        }
      }
    }

    connect()

    return () => {
      closedByEffect = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [enabled])
}
