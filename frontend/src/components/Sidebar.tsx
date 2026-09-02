import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import {
  LayoutDashboard,
  Bot,
  Sprout,
  Droplets,
  Wheat,
  Beaker,
  HeartPulse,
  MessageCircle,
  Bell,
  Settings,
  Leaf,
  TrendingUp,
} from 'lucide-react'

const items = [
  { to: '/dashboard', icon: LayoutDashboard, key: 'dashboard', end: true },
  { to: '/robot', icon: Bot, key: 'robot' },
  { to: '/monitoring', icon: Sprout, key: 'farm_monitoring' },
  { to: '/irrigation', icon: Droplets, key: 'irrigation' },
  { to: '/crop-recommendation', icon: Wheat, key: 'crop_recommendation' },
  { to: '/fertilizer', icon: Beaker, key: 'fertilizer' },
  { to: '/soil-health', icon: HeartPulse, key: 'soil_health' },
  { to: '/yield-prediction', icon: TrendingUp, key: 'yield_prediction' },
  { to: '/assistant', icon: MessageCircle, key: 'ai_assistant' },
  { to: '/alerts', icon: Bell, key: 'alerts' },
  { to: '/settings', icon: Settings, key: 'settings' },
]

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation()

  return (
    <div className="glass-panel m-3 flex h-[calc(100vh-1.5rem)] w-60 flex-col overflow-hidden rounded-2xl">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500 text-brand-900 live-pulse">
          <Leaf size={18} aria-hidden="true" />
        </div>
        <div>
          <p className="font-heading text-sm font-bold leading-tight text-[var(--text-primary)]">{t('app_name')}</p>
          <p className="text-[11px] leading-tight text-[var(--text-secondary)]">{t('tagline')}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
        {items.map(({ to, icon: Icon, key, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className="relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.span
                    layoutId="active-nav-pill"
                    className="absolute inset-0 rounded-xl bg-brand-50 shadow-[0_0_0_1px_rgba(123,224,91,0.3),0_0_16px_rgba(123,224,91,0.15)]"
                    transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                  />
                )}
                {!isActive && (
                  <span className="absolute inset-0 rounded-xl opacity-0 transition-opacity hover:opacity-100 hover:bg-[var(--bg-surface-muted)]" aria-hidden="true" />
                )}
                <span className={clsx('relative z-10 flex items-center gap-3', isActive && 'text-brand-700')}>
                  <Icon size={18} aria-hidden="true" />
                  {t(`nav.${key}`)}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
