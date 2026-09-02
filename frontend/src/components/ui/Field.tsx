import { cloneElement, isValidElement, useId, type InputHTMLAttributes, type ReactElement, type ReactNode, type SelectHTMLAttributes } from 'react'
import clsx from 'clsx'

const fieldBase =
  'w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2.5 text-sm text-[var(--text-primary)] outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100 disabled:cursor-not-allowed disabled:opacity-50'

export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return <label htmlFor={htmlFor} className="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]">{children}</label>
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
  const generatedId = useId()
  // Gives the label a real `htmlFor`/`id` association with its control for
  // screen readers and click-to-focus, without every call site needing to
  // pass its own id — only clones when the child doesn't already have one.
  const child = isValidElement(children)
    ? cloneElement(children as ReactElement<{ id?: string }>, {
        id: (children as ReactElement<{ id?: string }>).props.id ?? generatedId,
      })
    : children
  const childId = isValidElement(child) ? (child.props as { id?: string }).id : undefined

  return (
    <div>
      <Label htmlFor={childId}>{label}</Label>
      {child}
    </div>
  )
}
