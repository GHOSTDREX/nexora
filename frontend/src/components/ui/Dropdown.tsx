import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, ChevronDown } from 'lucide-react'

export interface DropdownOption {
  value: string
  label: string
}

/**
 * A custom, always-opens-below dropdown for long option lists (crops,
 * states, ...).
 *
 * Two problems with a native <select> here: the OS picker decides its own
 * position and flips upward when the trigger is near the bottom of the
 * viewport, and it can't be restyled to match the app. This renders its own
 * panel instead — but cards use `overflow-hidden` for their rounded
 * corners, which would clip a plain absolutely-positioned panel the moment
 * it grew past the card's edge. So the panel is portaled to <body> and
 * positioned with fixed coordinates computed from the trigger's own
 * bounding box, escaping any ancestor's overflow entirely.
 */
export function Dropdown({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string
  onChange: (value: string) => void
  options: DropdownOption[]
  placeholder?: string
}) {
  const [open, setOpen] = useState(false)
  const [rect, setRect] = useState<{ top: number; left: number; width: number; openUp: boolean } | null>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  const current = options.find((o) => o.value === value)

  function updateRect() {
    const el = triggerRef.current
    if (!el) return
    const box = el.getBoundingClientRect()
    const spaceBelow = window.innerHeight - box.bottom
    const openUp = spaceBelow < 260 && box.top > spaceBelow
    setRect({ top: openUp ? box.top : box.bottom, left: box.left, width: box.width, openUp })
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2.5 text-left text-sm text-[var(--text-primary)] outline-none transition hover:bg-[var(--bg-surface-muted)] focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
      >
        <span className={current ? '' : 'text-[var(--text-secondary)]'}>{current?.label ?? placeholder ?? 'Select…'}</span>
        <ChevronDown size={14} className="shrink-0 text-[var(--text-secondary)]" aria-hidden="true" />
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
                left: rect.left,
                width: rect.width,
              }}
              className="z-50 max-h-60 overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1 shadow-lg"
            >
              {options.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    onChange(opt.value)
                    setOpen(false)
                  }}
                  className="flex w-full items-center justify-between gap-2 px-3.5 py-2 text-left text-sm hover:bg-[var(--bg-surface-muted)]"
                >
                  <span className="text-[var(--text-primary)]">{opt.label}</span>
                  {opt.value === value && <Check size={14} className="shrink-0 text-brand-600" aria-hidden="true" />}
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
