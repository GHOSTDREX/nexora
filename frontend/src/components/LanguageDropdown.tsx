import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Globe, Check, ChevronDown } from 'lucide-react'
import { LANGUAGES } from '@/i18n'
import { useAuth } from '@/context/AuthContext'

export function LanguageDropdown({ compact = false }: { compact?: boolean }) {
  const { i18n } = useTranslation()
  const { user, updateLanguage } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const current = LANGUAGES.find((l) => l.code === i18n.language) ?? LANGUAGES[0]

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  async function pick(code: string) {
    setOpen(false)
    if (user) {
      await updateLanguage(code)
    } else {
      i18n.changeLanguage(code)
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Language"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-surface-muted)]"
      >
        <Globe size={16} className="text-brand-600" aria-hidden="true" />
        {!compact && <span className="font-medium">{current.nativeLabel}</span>}
        <ChevronDown size={14} className="text-[var(--text-secondary)]" aria-hidden="true" />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 z-50 mt-2 max-h-80 w-56 overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1.5 shadow-lg"
          >
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => pick(lang.code)}
                className="flex w-full items-center justify-between gap-2 px-3.5 py-2 text-left text-sm hover:bg-[var(--bg-surface-muted)]"
              >
                <span>
                  <span className="font-medium text-[var(--text-primary)]">{lang.nativeLabel}</span>
                  <span className="ml-2 text-xs text-[var(--text-secondary)]">{lang.label}</span>
                </span>
                {lang.code === current.code && <Check size={14} className="text-brand-600" aria-hidden="true" />}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
