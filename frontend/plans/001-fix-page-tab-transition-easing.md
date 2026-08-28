# 001 — Fix page/tab transition easing and exit gap

- **Status**: DONE
- **Commit**: n/a (repo is not under git version control)
- **Severity**: HIGH
- **Category**: Easing & duration / Purpose & frequency
- **Estimated scope**: 1 file (`frontend/src/lib/motion.ts`)

## Problem

`pageTransition` is the shared Framer Motion variant used for every route
change and every in-page tab switch in the app. Its exit phase uses
`ease: 'easeIn'`, which the animation playbook flags as always wrong on UI
(it starts slow, delaying the exact moment being watched) — and this is the
single highest-frequency animation in the app, since it fires on every
navigation and every tab click.

```ts
// src/lib/motion.ts:34-38 — current
export const pageTransition: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.28, ease: 'easeOut' } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.16, ease: 'easeIn' } },
}
```

Consumers, both unaffected by this plan (fixing the shared token fixes both):

- `src/components/PageTransition.tsx:10-20` — wraps `<Outlet />`, `AnimatePresence mode="wait"`, keyed by `location.pathname`. Fires on every route change.
- `src/pages/monitoring/MonitoringPage.tsx:92-93` — `AnimatePresence mode="wait"`, keyed by `tab`. Fires on every tab click within Farm Monitoring.

Because both use `mode="wait"`, the exiting content must fully finish its
exit transition before the entering content starts. A slow-starting
`easeIn` exit makes that gap feel even more sluggish than the raw duration
suggests.

## Target

Both `animate` and `exit` use the same strong ease-out curve (never `ease-in`
on UI), and the exit duration is shortened slightly so the `mode="wait"` gap
is barely perceptible without restructuring `AnimatePresence` mode (that
restructuring is out of scope for this plan — see Boundaries).

```ts
// target
const EASE_OUT: Transition['ease'] = [0.23, 1, 0.32, 1] // strong ease-out (cubic-bezier)

export const pageTransition: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.28, ease: EASE_OUT } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.12, ease: EASE_OUT } },
}
```

## Repo conventions to follow

- All shared Framer Motion variants already live in `src/lib/motion.ts` as
  named exports (`staggerContainer`, `staggerItem`, `cardHover`, `tapScale`,
  `pageTransition`, `revealOnScroll`) — add the new `EASE_OUT` constant in
  this same file, above `pageTransition`, not in a new file.
- The file already imports `type { Transition, Variants } from 'framer-motion'`
  (line 1) — reuse that import for the `Transition['ease']` type annotation,
  don't add a new import.
- No consumer file needs to change — `PageTransition.tsx` and
  `MonitoringPage.tsx` both reference `pageTransition` by name and inherit
  the fix automatically.

## Steps

1. In `src/lib/motion.ts`, add a new exported constant directly above the
   `pageTransition` export:
   ```ts
   const EASE_OUT: Transition['ease'] = [0.23, 1, 0.32, 1]
   ```
2. In the same file, change `pageTransition`'s `animate.transition.ease` from
   `'easeOut'` to `EASE_OUT`.
3. Change `pageTransition`'s `exit.transition.ease` from `'easeIn'` to
   `EASE_OUT`, and its `duration` from `0.16` to `0.12`.
4. Leave `initial`, `animate`'s `opacity`/`y` values, and `exit`'s
   `opacity`/`y` values unchanged — only the `ease` and exit `duration`
   change.

## Boundaries

- Do NOT touch `PageTransition.tsx` or `MonitoringPage.tsx` — the fix is
  entirely in the shared `lib/motion.ts` token.
- Do NOT change `AnimatePresence mode="wait"` to any other mode in either
  consumer — that is a separate, larger structural change (would need
  absolute positioning to avoid old/new content overlapping) and is out of
  scope here.
- Do NOT touch any other export in `lib/motion.ts` (`staggerContainer`,
  `staggerItem`, `cardHover`, `tapScale`, `revealOnScroll`) — those are
  separate findings, not part of this plan.
- Do NOT add new dependencies.
- If `pageTransition`'s current code doesn't match the excerpt above
  (drifted since this plan was written), STOP and report instead of
  improvising.

## Verification

- **Mechanical**: `cd frontend && npx tsc --noEmit` — expect no errors.
- **Feel check**: run the frontend dev server, log in, and:
  - Click between sidebar nav items (e.g. Dashboard → Robot → Irrigation)
    repeatedly. Confirm each page fades/slides in with a snappy start (not a
    slow, gradual one) and the previous page doesn't visibly linger.
  - Go to Farm Monitoring and click between the Soil / NPK / Environment
    tabs several times quickly. Confirm the blank gap between tabs feels
    brief, not sluggish.
  - In Chrome DevTools → More tools → Animations, set playback to 10% and
    trigger a navigation. Confirm the exit animation starts moving
    immediately (fast start = ease-out), not a slow ease-in creep.
  - Toggle `prefers-reduced-motion: reduce` in the Rendering panel and
    confirm navigation still works (this plan doesn't add reduced-motion
    handling — that's finding #2, a separate plan).
- **Done when**: `lib/motion.ts`'s `pageTransition.exit.transition.ease` is
  no longer `'easeIn'` anywhere in the codebase, `tsc --noEmit` passes, and
  the feel-check above holds on both PageTransition and MonitoringPage tab
  switches.
