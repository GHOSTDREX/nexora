import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Globe, Check, ChevronDown } from 'lucide-react'
import { LANGUAGES } from '@/i18n'
import { useAuth } from '@/context/AuthContext'

// Panel is portaled to <body> and positioned from the trigger's own bounding
// box — same fix as components/ui/Dropdown.tsx, for the same reason: cards
// use overflow-hidden for their rounded corners, which clips a plain
// absolutely-positioned panel (this menu is often used inside one, e.g. the
// Settings page's Profile card).
export function LanguageDropdown({ compact = false }: { compact?: boolean }) {
  const { i18n } = useTranslation()
  const { user, updateLanguage } = useAuth()
  const [open, setOpen] = useState(false)
  const [rect, setRect] = useState<{ top: number; right: number; openUp: boolean } | null>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  const current = LANGUAGES.find((l) => l.code === i18n.language) ?? LANGUAGES[0]

  function updateRect() {
    const el = triggerRef.current
    if (!el) return
    const box = el.getBoundingClientRect()
    const spaceBelow = window.innerHeight - box.bottom
    const openUp = spaceBelow < 320 && box.top > spaceBelow
    setRect({ top: openUp ? box.top : box.bottom, right: window.innerWidth - box.right, openUp })
  }

  useEffect(() => {
    if (!open) return
    updateRect()
    function onOutside(e: MouseEvent) {
      const target = e.target as Node
      if (triggerRef.current?.contains(target)) return
      if (panelRef.current?.contains(target)) return
      setOpen(false)
    }
    document.addEventListener('mousedown', onOutside)
    window.addEventListener('resize', updateRect)
    window.addEventListener('scroll', updateRect, true)
    return () => {
      document.removeEventListener('mousedown', onOutside)
      window.removeEventListener('resize', updateRect)
      window.removeEventListener('scroll', updateRect, true)
    }
  }, [open])

  async function pick(code: string) {
    setOpen(false)
    if (user) {
      await updateLanguage(code)
    } else {
      i18n.changeLanguage(code)
    }
  }

  return (
    <>
      <button
        ref={triggerRef}
        onClick={() => setOpen((o) => !o)}
        aria-label="Language"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-surface-muted)]"
      >
        <Globe size={16} className="text-brand-600" aria-hidden="true" />
        {!compact && <span className="font-medium">{current.nativeLabel}</span>}
        <ChevronDown size={14} className="text-[var(--text-secondary)]" aria-hidden="true" />
      </button>

      {rect && createPortal(
        <AnimatePresence>
          {open && (
            <motion.div
              ref={panelRef}
              initial={{ opacity: 0, y: rect.openUp ? 6 : -6, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: rect.openUp ? 6 : -6, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              style={{
                position: 'fixed',
                top: rect.openUp ? undefined : rect.top + 8,
                bottom: rect.openUp ? window.innerHeight - rect.top + 8 : undefined,
                right: rect.right,
              }}
              className="z-50 max-h-80 w-56 overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1.5 shadow-lg"
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
        </AnimatePresence>,
        document.body,
      )}
    </>
  )
}
