# 003 — Give LanguageDropdown and Dropdown matching open/close motion

- **Status**: DONE
- **Commit**: n/a (repo is not under git version control)
- **Severity**: MEDIUM
- **Category**: Cohesion / Missed opportunity
- **Estimated scope**: 2 files (`LanguageDropdown.tsx`, `components/ui/Dropdown.tsx`)

## Problem

`Topbar.tsx:85-106`'s account-menu popover fades+slides+scales in over
150ms via `AnimatePresence`/`motion.div`. Two other anchored popovers in the
app show/hide with a bare conditional render and no transition at all —
same UI pattern, inconsistent motion:

```tsx
// src/components/LanguageDropdown.tsx:45-46 — current
{open && (
  <div className="absolute right-0 z-50 mt-2 max-h-80 w-56 overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1.5 shadow-lg">
```

```tsx
// src/components/ui/Dropdown.tsx:83-95 — current
{open && rect && createPortal(
  <div
    ref={panelRef}
    style={{ ... }}
    className="z-50 max-h-60 overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1 shadow-lg"
  >
```

## Target

Same treatment as `Topbar.tsx`'s account menu: `opacity: 0 → 1`,
`y: -6 → 0`, `scale: 0.97 → 1`, `duration: 0.15`. `Dropdown.tsx` can open
either below or above its trigger (`rect.openUp`), so its slide direction
must match — sliding in from the trigger side, not always from above.

```tsx
// target — LanguageDropdown.tsx
<AnimatePresence>
  {open && (
    <motion.div
      initial={{ opacity: 0, y: -6, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -6, scale: 0.97 }}
      transition={{ duration: 0.15 }}
      className="absolute right-0 z-50 mt-2 max-h-80 w-56 overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1.5 shadow-lg"
    >
      {/* unchanged children */}
    </motion.div>
  )}
</AnimatePresence>
```

```tsx
// target — components/ui/Dropdown.tsx (openUp-aware direction)
{open && rect && createPortal(
  <AnimatePresence>
    <motion.div
      key="panel"
      ref={panelRef}
      initial={{ opacity: 0, y: rect.openUp ? 6 : -6, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: rect.openUp ? 6 : -6, scale: 0.97 }}
      transition={{ duration: 0.15 }}
      style={{ ... }} // unchanged
      className="z-50 max-h-60 overflow-y-auto rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] py-1 shadow-lg"
    >
      {/* unchanged children */}
    </motion.div>
  </AnimatePresence>,
  document.body,
)}
```

## Repo conventions to follow

- `Topbar.tsx:87-92` is the exemplar this plan copies — same opacity/y/scale
  values and duration, for exact visual consistency across every popover in
  the app.
- Both files already import from `framer-motion`; `LanguageDropdown.tsx`
  needs `motion` and `AnimatePresence` added to its React import line;
  `Dropdown.tsx` needs the same (it currently only imports `createPortal`
  from `react-dom`, no framer-motion import yet).

## Steps

1. In `src/components/LanguageDropdown.tsx`:
   - Add `motion, AnimatePresence` to the top-level import (there is
     currently no `framer-motion` import in this file — add
     `import { motion, AnimatePresence } from 'framer-motion'`).
   - Wrap the existing `{open && (<div className="absolute right-0 z-50 mt-2 ...">...)}` block in `<AnimatePresence>`.
   - Change the `<div>` to `<motion.div>` and add
     `initial={{ opacity: 0, y: -6, scale: 0.97 }}`,
     `animate={{ opacity: 1, y: 0, scale: 1 }}`,
     `exit={{ opacity: 0, y: -6, scale: 0.97 }}`,
     `transition={{ duration: 0.15 }}`.
   - Leave the `className` and every child element unchanged.
2. In `src/components/ui/Dropdown.tsx`:
   - Add `import { motion, AnimatePresence } from 'framer-motion'` near the
     existing `import { createPortal } from 'react-dom'` line.
   - Wrap the panel currently passed to `createPortal(...)` in
     `<AnimatePresence>`.
   - Change the panel's outer `<div ref={panelRef} ...>` to
     `<motion.div key="panel" ref={panelRef} ...>` and add
     `initial={{ opacity: 0, y: rect.openUp ? 6 : -6, scale: 0.97 }}`,
     `animate={{ opacity: 1, y: 0, scale: 1 }}`,
     `exit={{ opacity: 0, y: rect.openUp ? 6 : -6, scale: 0.97 }}`,
     `transition={{ duration: 0.15 }}`.
   - Leave the existing `style={{ position: 'fixed', ... }}` object and
     `className` unchanged — they still control fixed positioning.

## Boundaries

- Do NOT change the outside-click-close logic, positioning math
  (`updateRect`), or the `openUp` flip threshold in `Dropdown.tsx`.
- Do NOT touch `Topbar.tsx` — it's already correct and is the exemplar.
- Do NOT add a search box back to `Dropdown.tsx` (removed per explicit user
  request in an earlier session) or otherwise change its option-list
  behavior — motion only.
- Do NOT add new dependencies — `framer-motion` is already a project
  dependency.
- If either file's current code doesn't match the excerpts shown, STOP and
  report instead of improvising.

## Verification

- **Mechanical**: `cd frontend && npx tsc --noEmit` — expect no errors.
- **Feel check**:
  - Open the language dropdown (Topbar globe icon, or Settings page): it
    should now fade+slide+scale in the same way the account menu does, and
    animate back out on close/outside-click instead of vanishing instantly.
  - On Crop Recommendation, open the crop dropdown: same fade-in feel,
    opening from below the trigger.
  - On Yield Prediction, scroll so the crop/state dropdown trigger sits near
    the bottom of the viewport and open it — confirm it flips to open
    upward (`openUp`) and slides in from *below* (sliding up into place),
    not from above.
  - In DevTools Animations panel at 10% playback, confirm both panels scale
    from ~0.97, not from 0, and don't overshoot past 1.0.
- **Done when**: both dropdowns animate in/out with the Topbar menu's exact
  timing, the upward-opening case slides from the correct side, and
  `tsc --noEmit` passes.
