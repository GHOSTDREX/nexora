import { Moon, Sun } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTheme } from '@/context/ThemeContext'

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <motion.button
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.95 }}
      transition={{ duration: 0.15 }}
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className={
        compact
          ? 'flex rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-2.5 text-[var(--text-primary)] hover:bg-[var(--bg-surface-muted)]'
          : 'flex items-center gap-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-surface-muted)]'
      }
    >
      {isDark ? <Sun size={compact ? 17 : 16} aria-hidden="true" /> : <Moon size={compact ? 17 : 16} aria-hidden="true" />}
      {!compact && <span className="font-medium">{isDark ? 'Light mode' : 'Dark mode'}</span>}
    </motion.button>
  )
}
