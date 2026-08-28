# 004 — Replace staggerItem's overshoot easing with the app's ease-out

- **Status**: DONE
- **Commit**: n/a (repo is not under git version control)
- **Severity**: MEDIUM
- **Category**: Cohesion & physicality
- **Estimated scope**: 1 file (`lib/motion.ts`)

## Problem

```ts
// src/lib/motion.ts:11-19 — current
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 16, scale: 0.96 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.4, ease: [0.34, 1.36, 0.64, 1] } satisfies Transition,
  },
}
```

`[0.34, 1.36, 0.64, 1]` is a "back" curve with overshoot (the `1.36` y-value
exceeds 1, so scale/position briefly overshoot past their final value before
settling). This fires via `StatCard.tsx:50` on every stat-card grid —
`Dashboard.tsx`, `Alerts.tsx`, `RobotPage.tsx`, and `ManualSensorForm.tsx` —
several of which (Dashboard especially) load on nearly every session. A
springy overshoot reads as playful/consumer-app personality, which doesn't
match AgriNova's otherwise crisp, professional dashboard tone (per its
"Verdant Intelligence" design system). Bounce should be reserved for rare,
playful moments, not a grid the user sees constantly.

## Target

Reuse the same strong ease-out introduced in plan 001
(`cubic-bezier(0.23, 1, 0.32, 1)`, no overshoot) instead of a bespoke
overshoot curve:

```ts
// target
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 16, scale: 0.96 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.4, ease: EASE_OUT } satisfies Transition,
  },
}
```

## Repo conventions to follow

- `EASE_OUT` is already defined in this same file by plan 001 (directly
  above `pageTransition`) — reuse that constant, don't redefine it.
- Apply plans in order (001 before this one) since this plan depends on
  `EASE_OUT` existing.

## Steps

1. In `src/lib/motion.ts`, in the `staggerItem` export's `show.transition`,
   change `ease: [0.34, 1.36, 0.64, 1]` to `ease: EASE_OUT`.
2. Leave `duration: 0.4`, `hidden`, and every other property unchanged.

## Boundaries

- Do NOT change `staggerContainer` (the `staggerChildren`/`delayChildren`
  timing is unrelated to this finding).
- Do NOT touch `StatCard.tsx` or any of its four consumer pages — the fix
  is entirely in the shared `staggerItem` token.
- Do NOT change `cardHover`'s easing (`easeOut` already, separate export,
  not part of this finding).
- Do NOT add new dependencies.
- If `staggerItem`'s current code doesn't match the excerpt above, STOP and
  report instead of improvising.

## Verification

- **Mechanical**: `cd frontend && npx tsc --noEmit` — expect no errors.
- **Feel check**:
  - Load the Dashboard (or Alerts, or Robot page) and watch the stat cards
    animate in. Confirm each card settles directly into place — no visible
    overshoot/wobble past its final size or position.
  - In DevTools Animations panel at 10% playback, confirm the scale curve
    approaches 1.0 smoothly from below without crossing past it.
  - Compare side-by-side (undo the change locally, reload, redo) if the
    difference isn't obvious at full speed — the old curve has a distinct
    little "pop" past full size right before settling; the new one doesn't.
- **Done when**: `staggerItem.show.transition.ease` is `EASE_OUT` (no
  bespoke overshoot array remains in the file), `tsc --noEmit` passes, and
  the feel-check shows no overshoot on any stat-card grid.
