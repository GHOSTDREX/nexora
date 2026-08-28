# 002 — Fix reduced-motion coverage

- **Status**: DONE
- **Commit**: n/a (repo is not under git version control)
- **Severity**: MEDIUM
- **Category**: Accessibility
- **Estimated scope**: 3 files (`index.css`, `lib/motion.ts`, `PageTransition.tsx`, `monitoring/MonitoringPage.tsx`)

## Problem

```css
/* src/index.css:220-227 — current */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

This zeroes every CSS `transition`, not just movement — contradicting "keep
transitions that aid comprehension, remove position changes... not zero."

Separately, this global CSS rule does nothing for Framer Motion animations
(the JS-driven kind), which is most of the app's motion — 24 files import
`framer-motion`. Only `components/ui/AnimatedNumber.tsx` and
`components/ui/beams-background.tsx` currently call `useReducedMotion()`.
The highest-frequency Framer animation, `pageTransition` (fixed in plan
001), has no reduced-motion branch at all.

## Target

```css
/* target — src/index.css:220-227 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
  }
}
```

(Drops the `transition-duration: 0.01ms !important` line only — this
codebase has no `transition: all`, so existing CSS transitions are already
narrow, mostly hover-color changes that should keep their eased feedback.
`animation-duration`/`animation-iteration-count` stay zeroed, which correctly
kills the two infinite decorative keyframes: `.live-pulse` and `.ai-glow`.)

```ts
// target — src/lib/motion.ts, new export alongside pageTransition
export const pageTransitionReduced: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.28, ease: EASE_OUT } },
  exit: { opacity: 0, transition: { duration: 0.12, ease: EASE_OUT } },
}
```

```tsx
// target — src/components/PageTransition.tsx
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { pageTransition, pageTransitionReduced } from '@/lib/motion'

export function PageTransition({ children }: { children: ReactNode }) {
  const location = useLocation()
  const reduceMotion = useReducedMotion()

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        variants={reduceMotion ? pageTransitionReduced : pageTransition}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
```

Same `reduceMotion ? pageTransitionReduced : pageTransition` swap applies to
the `variants={pageTransition}` on `src/pages/monitoring/MonitoringPage.tsx:93`.

## Repo conventions to follow

- `pageTransition` already lives in `src/lib/motion.ts` as a named export
  (fixed in plan 001, which added the `EASE_OUT` constant this plan reuses)
  — add `pageTransitionReduced` right below it, same file.
- `components/ui/AnimatedNumber.tsx:16` is the existing exemplar for calling
  `useReducedMotion()` from `framer-motion` in this codebase — import it the
  same way.

## Steps

1. In `src/index.css`, inside the `@media (prefers-reduced-motion: reduce)`
   block (currently lines 220-227), delete the line
   `transition-duration: 0.01ms !important;`. Keep the other three
   declarations (`animation-duration`, `animation-iteration-count`,
   `scroll-behavior`) exactly as they are.
2. In `src/lib/motion.ts`, directly below the `pageTransition` export, add:
   ```ts
   export const pageTransitionReduced: Variants = {
     initial: { opacity: 0 },
     animate: { opacity: 1, transition: { duration: 0.28, ease: EASE_OUT } },
     exit: { opacity: 0, transition: { duration: 0.12, ease: EASE_OUT } },
   }
   ```
3. In `src/components/PageTransition.tsx`:
   - Change the import on line 3 from `import { AnimatePresence, motion } from 'framer-motion'` to `import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'`.
   - Change the import on line 4 from `import { pageTransition } from '@/lib/motion'` to `import { pageTransition, pageTransitionReduced } from '@/lib/motion'`.
   - Inside the component body, add `const reduceMotion = useReducedMotion()` before the `return`.
   - Change `variants={pageTransition}` to `variants={reduceMotion ? pageTransitionReduced : pageTransition}`.
4. In `src/pages/monitoring/MonitoringPage.tsx`:
   - Add `useReducedMotion` to the existing `framer-motion` import (line 3).
   - Add `pageTransitionReduced` to the existing `@/lib/motion` import (wherever `pageTransition` is currently imported from).
   - Add `const reduceMotion = useReducedMotion()` inside the component body.
   - Change `variants={pageTransition}` (around line 93) to `variants={reduceMotion ? pageTransitionReduced : pageTransition}`.

## Boundaries

- Do NOT add `useReducedMotion()` branches to every Framer Motion consumer
  in the app — that's disproportionate scope for one plan. This plan covers
  only the CSS blanket rule and the single highest-frequency Framer
  animation (`pageTransition`, used by route changes and Farm Monitoring
  tabs). `staggerItem`'s motion is addressed separately by plan 004, which
  already makes it gentler by removing its overshoot easing.
- Do NOT touch `AnimatedNumber.tsx` or `beams-background.tsx` — they already
  handle reduced motion correctly.
- Do NOT remove the `.live-pulse` / `.ai-glow` keyframe animations, only
  ensure they stay killed under reduced motion (they already are).
- Do NOT add new dependencies.
- If the current code at any cited location doesn't match the excerpt
  shown, STOP and report instead of improvising.

## Verification

- **Mechanical**: `cd frontend && npx tsc --noEmit` — expect no errors.
- **Feel check**:
  - In Chrome DevTools → Rendering panel, set "Emulate CSS media feature
    prefers-reduced-motion" to `reduce`.
  - Navigate between pages and switch Farm Monitoring tabs: confirm content
    still cross-fades (opacity) but no longer slides vertically.
  - Hover a button or the theme toggle: confirm the hover color/background
    transition still eases smoothly (not an instant snap) — this is the
    "kept" feedback the CSS fix restores.
  - Find a `.live-pulse` indicator (e.g. Dashboard's live sensor badge):
    confirm the pulsing ring animation does not play under reduced motion.
  - Turn `prefers-reduced-motion` back to "No emulation" and confirm page
    transitions and tab switches look identical to before this plan (normal
    fade + slight vertical slide).
- **Done when**: `transition-duration` no longer appears in the
  `prefers-reduced-motion` media block, `PageTransition.tsx` and
  `MonitoringPage.tsx` both branch on `useReducedMotion()`, `tsc --noEmit`
  passes, and the feel-check above holds in both motion states.
