import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'
import clsx from 'clsx'

const fieldBase =
  'w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2.5 text-sm text-[var(--text-primary)] outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100'

export function Label({ children }: { children: ReactNode }) {
  return <label className="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]">{children}</label>
}

export function Input({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={clsx(fieldBase, className)} {...rest} />
}

export function Select({ className, children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={clsx(fieldBase, 'cursor-pointer', className)} {...rest}>
      {children}
    </select>
  )
}

export function FieldGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
    </div>
  )
}
