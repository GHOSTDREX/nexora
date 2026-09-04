import type { ReactNode } from 'react'
import { motion, type HTMLMotionProps } from 'framer-motion'
import clsx from 'clsx'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg' | 'icon'

const variantClasses: Record<Variant, string> = {
  primary: 'bg-brand-500 text-brand-900 hover:brightness-90 shadow-sm shadow-brand-900/30 font-semibold',
  secondary: 'bg-[var(--bg-surface)] text-brand-700 border-2 border-brand-200 hover:bg-brand-50 hover:border-brand-300 shadow-sm',
  ghost: 'bg-transparent text-[var(--text-primary)] hover:bg-[var(--bg-surface-muted)]',
  danger: 'bg-red-600 text-white hover:bg-red-700',
}

const sizeClasses: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-sm',
  // Icon-only controls (no visible text) need a real touch target even
  // when the icon itself is small — h-11/w-11 = 44px, the mobile minimum.
  icon: 'h-11 w-11 p-0 text-sm',
}

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  variant?: Variant
  size?: Size
  isLoading?: boolean
  children?: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading,
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || isLoading

  return (
    <motion.button
      whileHover={isDisabled ? undefined : { y: -1 }}
      whileTap={isDisabled ? undefined : { scale: 0.97 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      disabled={isDisabled}
      {...rest}
    >
      {isLoading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden="true" />
      )}
      {children}
    </motion.button>
  )
}
