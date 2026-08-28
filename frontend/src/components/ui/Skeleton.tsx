import clsx from 'clsx'

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse rounded-lg bg-[var(--bg-surface-muted)]', className)} />
}
