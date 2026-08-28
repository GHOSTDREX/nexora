import type { HTMLAttributes, ReactNode } from 'react'
import clsx from 'clsx'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Adds a subtle lift + shadow on hover — use for interactive/scannable cards. */
  interactive?: boolean
}

export function Card({ className, children, interactive, ...rest }: CardProps) {
  return (
    <div
      className={clsx(
        'glass-panel overflow-hidden rounded-2xl transition-[transform,box-shadow] duration-200 ease-out',
        interactive && 'hover:-translate-y-0.5 hover:border-brand-300/40',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, action }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 px-5 pt-5">
      <div>
        <h3 className="font-heading text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-[var(--text-secondary)]">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
