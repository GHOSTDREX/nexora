import axios from 'axios'

// Default to whatever host the page was loaded from (localhost in normal
// dev, the PC's LAN IP when opened from a phone) so no rebuild/env var is
// needed to switch between them; VITE_API_URL/VITE_WS_URL still override.
const backendHost = `${window.location.hostname}:8000`
export const API_URL = import.meta.env.VITE_API_URL ?? `http://${backendHost}`
export const WS_URL = import.meta.env.VITE_WS_URL ?? `ws://${backendHost}`

const TOKEN_KEY = 'agrinova_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearToken()
      const publicPaths = ['/', '/login', '/register']
      if (!publicPaths.includes(window.location.pathname)) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export function apiErrorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (detail?.message) return detail.message
    if (Array.isArray(detail) && detail.length > 0) {
      const messages = detail.map((item) => {
        const field = Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : null
        return field && item?.msg ? `${field}: ${item.msg}` : item?.msg
      }).filter(Boolean)
      if (messages.length > 0) return messages.join('; ')
    }
  }
  return fallback
}
