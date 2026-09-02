import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { cardHover, staggerItem } from '@/lib/motion'
import { AnimatedNumber } from '@/components/ui/AnimatedNumber'

export function StatCard({
  icon,
  label,
  value,
  numericValue,
  decimals = 0,
  unit,
  tone = 'neutral',
  live,
}: {
  icon: ReactNode
  label: string
  value: ReactNode
  numericValue?: number
  decimals?: number
  unit?: string
  tone?: 'brand' | 'gold' | 'water' | 'amber' | 'neutral'
  live?: boolean
}) {
  const toneBar: Record<string, string> = {
    brand: 'bg-brand-500',
    gold: 'bg-gold-500',
    water: 'bg-water-500',
    amber: 'bg-amber-500',
    neutral: 'bg-slate-300',
  }
  const toneIcon: Record<string, string> = {
    brand: 'bg-brand-500 text-brand-900 shadow-brand-900/30',
    gold: 'bg-gold-400 text-brand-900 shadow-black/30',
    water: 'bg-water-400 text-brand-900 shadow-black/30',
    amber: 'bg-amber-400 text-brand-900 shadow-black/30',
    neutral: 'bg-slate-600 text-slate-100 shadow-black/20',
  }
  const toneValue: Record<string, string> = {
    brand: 'text-brand-700',
    gold: 'text-gold-700',
    water: 'text-water-700',
    amber: 'text-amber-400',
    neutral: 'text-[var(--text-primary)]',
  }

  return (
    <motion.div
      variants={{ ...staggerItem, hover: cardHover.hover }}
      whileHover="hover"
      className="relative overflow-hidden rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4"
    >
      <div className={clsx('absolute inset-x-0 top-0 h-1', toneBar[tone])} aria-hidden="true" />
      <div className="flex items-start justify-between">
        <div className={clsx('flex h-9 w-9 items-center justify-center rounded-xl shadow-sm', toneIcon[tone])} aria-hidden="true">
          {icon}
        </div>
        {live && <span className="live-pulse h-2 w-2 rounded-full bg-brand-500" aria-hidden="true" title="Live" />}
      </div>
      <p className="mt-3 text-xs font-medium text-[var(--text-secondary)]">{label}</p>
      <p className={clsx('font-heading mt-0.5 text-xl font-bold', toneValue[tone])}>
        {typeof numericValue === 'number' ? <AnimatedNumber value={numericValue} decimals={decimals} /> : value}
        {unit && <span className="ml-1 font-sans text-sm font-medium text-[var(--text-secondary)]">{unit}</span>}
      </p>
    </motion.div>
  )
}
