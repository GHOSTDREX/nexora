import type { ReactNode } from 'react'
import clsx from 'clsx'

type Tone = 'brand' | 'neutral' | 'warning' | 'critical' | 'info' | 'ai'

const toneClasses: Record<Tone, string> = {
  brand: 'bg-brand-100 text-brand-700',
  neutral: 'bg-[var(--bg-surface-muted)] text-[var(--text-secondary)]',
  warning: 'bg-amber-100 text-amber-800',
  critical: 'bg-red-100 text-red-700',
  info: 'bg-water-100 text-water-700',
  ai: 'bg-ai-100 text-ai-400',
}

export function Badge({ tone = 'neutral', children, dot }: { tone?: Tone; children: ReactNode; dot?: boolean }) {
  return (
    <span className={clsx('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium', toneClasses[tone])}>
      {dot && <span className={clsx('h-1.5 w-1.5 rounded-full', {
        'bg-brand-500': tone === 'brand',
        'bg-slate-400': tone === 'neutral',
        'bg-amber-500': tone === 'warning',
        'bg-red-500': tone === 'critical',
        'bg-water-500': tone === 'info',
        'bg-ai-400': tone === 'ai',
      })} />}
      {children}
    </span>
  )
}
