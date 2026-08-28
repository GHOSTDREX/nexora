import type { ReactNode } from 'react'
import clsx from 'clsx'

const toneClasses = {
  brand: 'bg-brand-500 text-brand-900 shadow-brand-900/30',
  gold: 'bg-gold-400 text-brand-900 shadow-black/30',
  water: 'bg-water-400 text-brand-900 shadow-black/30',
  amber: 'bg-amber-400 text-brand-900 shadow-black/30',
  neutral: 'bg-slate-600 text-slate-100 shadow-black/20',
} as const

export function IconBadge({
  icon,
  tone = 'brand',
  size = 'sm',
}: {
  icon: ReactNode
  tone?: keyof typeof toneClasses
  size?: 'sm' | 'md'
}) {
  return (
    <div
      className={clsx(
        'flex shrink-0 items-center justify-center rounded-xl shadow-sm',
        size === 'sm' ? 'h-8 w-8' : 'h-10 w-10',
        toneClasses[tone],
      )}
      aria-hidden="true"
    >
      {icon}
    </div>
  )
}
