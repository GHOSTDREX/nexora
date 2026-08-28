import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, Bell, LogOut, User as UserIcon } from 'lucide-react'
import { LanguageDropdown } from '@/components/LanguageDropdown'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useAuth } from '@/context/AuthContext'
import { useFarmData } from '@/context/FarmDataContext'

export function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { t } = useTranslation()
  const { user, farm, logout } = useAuth()
  const { unreadCount } = useFarmData()
  const [menuOpen, setMenuOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  return (
    <header className="relative z-30 flex h-16 items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/80 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          aria-label="Open menu"
          className="rounded-lg p-2 transition-colors hover:bg-[var(--bg-surface-muted)] lg:hidden"
        >
          <Menu size={20} aria-hidden="true" />
        </button>
        <div className="hidden sm:block">
          <p className="font-heading text-sm font-semibold text-[var(--text-primary)]">{farm?.name ?? '—'}</p>
          <p className="text-xs text-[var(--text-secondary)]">{farm?.region}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <ThemeToggle compact />
        <LanguageDropdown compact />

        <motion.div whileHover={{ y: -1 }} whileTap={{ scale: 0.95 }} transition={{ duration: 0.15 }}>
          <Link
            to="/alerts"
            aria-label={`${t('nav.alerts')}${unreadCount > 0 ? ` — ${unreadCount} unread` : ''}`}
            className="relative flex rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-2.5 hover:bg-[var(--bg-surface-muted)]"
          >
            <Bell size={17} aria-hidden="true" />
            <AnimatePresence>
              {unreadCount > 0 && (
                <motion.span
                  key={unreadCount}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.5, opacity: 0 }}
                  aria-hidden="true"
                  className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
                >
                  {unreadCount > 9 ? '9+' : unreadCount}
                </motion.span>
              )}
            </AnimatePresence>
            <span className="sr-only" role="status" aria-atomic="true">
              {unreadCount} unread alerts
            </span>
          </Link>
        </motion.div>

        <div className="relative" ref={ref}>
          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.95 }}
            transition={{ duration: 0.15 }}
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Account menu"
            aria-expanded={menuOpen}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700"
          >
            {user?.full_name?.[0]?.toUpperCase() ?? <UserIcon size={16} aria-hidden="true" />}
          </motion.button>
          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, y: -6, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 0.97 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 z-50 mt-2 w-48 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1.5 shadow-lg"
              >
                <div className="px-3.5 py-2 text-xs text-[var(--text-secondary)]">
                  <p className="truncate font-medium text-[var(--text-primary)]">{user?.full_name}</p>
                  <p className="truncate">{user?.email}</p>
                </div>
                <button
                  onClick={logout}
                  className="flex w-full items-center gap-2 px-3.5 py-2 text-left text-sm text-red-400 hover:bg-red-500/10"
                >
                  <LogOut size={15} aria-hidden="true" /> {t('common.logout')}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  )
}
