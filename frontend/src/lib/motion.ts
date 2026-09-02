import type { Transition, Variants } from 'framer-motion'

const EASE_OUT: Transition['ease'] = [0.23, 1, 0.32, 1] // strong ease-out (cubic-bezier)

/** Stagger container for grids/lists — children fade+rise in a soft wave. */
export const staggerContainer: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.06, delayChildren: 0.02 },
  },
}

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 16, scale: 0.96 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.4, ease: EASE_OUT } satisfies Transition,
  },
}

/** Card hover-lift — transform/opacity only, stays on the compositor thread.
 * Used by StatCard; Card's own `interactive` prop deliberately stays a
 * lighter, CSS-only lift since it's applied to dozens of larger panels. */
export const cardHover = {
  rest: { y: 0, scale: 1, boxShadow: '0 1px 2px rgba(15,61,34,0.04)' },
  hover: {
    y: -4,
    scale: 1.015,
    boxShadow: '0 0 0 1px rgba(123,224,91,0.25), 0 16px 32px rgba(0,0,0,0.4)',
    transition: { duration: 0.22, ease: 'easeOut' },
  },
}

export const tapScale = { scale: 0.97 }

export const pageTransition: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.28, ease: EASE_OUT } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.12, ease: EASE_OUT } },
}

/** Reduced-motion counterpart to pageTransition — opacity only, no movement. */
export const pageTransitionReduced: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.28, ease: EASE_OUT } },
  exit: { opacity: 0, transition: { duration: 0.12, ease: EASE_OUT } },
}

/** Scroll-triggered reveal for marketing sections — pairs with `whileInView` + `viewport={{ once: true }}`. */
export const revealOnScroll: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
}
