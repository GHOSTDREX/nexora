import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { api, clearToken, setToken as persistToken } from '@/lib/api'
import type { Farm, User } from '@/lib/types'

interface AuthContextValue {
  user: User | null
  farm: Farm | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (fullName: string, email: string, password: string, language: string) => Promise<void>
  logout: () => void
  refreshFarm: () => Promise<void>
  setFarm: (farm: Farm) => void
  updateLanguage: (language: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [farm, setFarmState] = useState<Farm | null>(null)
  const [loading, setLoading] = useState(true)
  const { i18n } = useTranslation()

  const bootstrap = useCallback(async () => {
    try {
      const { data: me } = await api.get<User>('/api/auth/me')
      setUser(me)
      i18n.changeLanguage(me.preferred_language)
      try {
        const { data: farmData } = await api.get<Farm>('/api/farm')
        setFarmState(farmData)
      } catch {
        setFarmState(null)
      }
    } catch {
      setUser(null)
      setFarmState(null)
    } finally {
      setLoading(false)
    }
  }, [i18n])

  useEffect(() => {
    bootstrap()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(
    async (email: string, password: string) => {
      const { data } = await api.post('/api/auth/login', { email, password })
      persistToken(data.access_token)
      await bootstrap()
    },
    [bootstrap],
  )

  const register = useCallback(
    async (fullName: string, email: string, password: string, language: string) => {
      const { data } = await api.post('/api/auth/register', {
        full_name: fullName,
        email,
        password,
        preferred_language: language,
      })
      persistToken(data.access_token)
      await bootstrap()
    },
    [bootstrap],
  )

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    setFarmState(null)
  }, [])

  const refreshFarm = useCallback(async () => {
    try {
      const { data } = await api.get<Farm>('/api/farm')
      setFarmState(data)
    } catch {
      setFarmState(null)
    }
  }, [])

  const updateLanguage = useCallback(
    async (language: string) => {
      i18n.changeLanguage(language)
      try {
        await api.patch('/api/auth/me/language', { preferred_language: language })
        setUser((prev) => (prev ? { ...prev, preferred_language: language } : prev))
      } catch {
        // UI already switched language locally; persisting the preference
        // server-side is best-effort and shouldn't block/crash the switch.
      }
    },
    [i18n],
  )

  return (
    <AuthContext.Provider
      value={{ user, farm, loading, login, register, logout, refreshFarm, setFarm: setFarmState, updateLanguage }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
