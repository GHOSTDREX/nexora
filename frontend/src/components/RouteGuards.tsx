import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Leaf } from 'lucide-react'

function FullscreenLoader() {
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-[var(--bg-app)]">
      <div className="flex flex-col items-center gap-3">
        <div className="flex h-12 w-12 animate-pulse items-center justify-center rounded-2xl bg-brand-500 text-brand-900">
          <Leaf size={22} aria-hidden="true" />
        </div>
        <p className="text-sm text-[var(--text-secondary)]">Loading AgriNova…</p>
      </div>
    </div>
  )
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, farm, loading } = useAuth()
  if (loading) return <FullscreenLoader />
  if (!user) return <Navigate to="/login" replace />
  if (!farm) return <Navigate to="/onboarding" replace />
  return <>{children}</>
}

export function RequireOnboarding({ children }: { children: ReactNode }) {
  const { user, farm, loading } = useAuth()
  if (loading) return <FullscreenLoader />
  if (!user) return <Navigate to="/login" replace />
  if (farm) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { user, farm, loading } = useAuth()
  if (loading) return <FullscreenLoader />
  if (user && farm) return <Navigate to="/dashboard" replace />
  if (user && !farm) return <Navigate to="/onboarding" replace />
  return <>{children}</>
}
