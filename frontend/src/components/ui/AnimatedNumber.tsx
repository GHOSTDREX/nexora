import { useEffect, useRef, useState } from 'react'
import { animate, useReducedMotion } from 'framer-motion'

/** Smoothly counts from the previous value to a new one whenever it changes. */
export function AnimatedNumber({
  value,
  decimals = 0,
  suffix = '',
}: {
  value: number
  decimals?: number
  suffix?: string
}) {
  const [display, setDisplay] = useState(value)
  const prevRef = useRef(value)
  const reduceMotion = useReducedMotion()

  useEffect(() => {
    if (reduceMotion || !Number.isFinite(value)) {
      setDisplay(value)
      prevRef.current = value
      return
    }
    const from = prevRef.current
    const controls = animate(from, value, {
      duration: 0.6,
      ease: 'easeOut',
      onUpdate: (v) => setDisplay(v),
    })
    prevRef.current = value
    return () => controls.stop()
  }, [value, reduceMotion])

  if (!Number.isFinite(value)) return <>—</>

  return (
    <>
      {display.toFixed(decimals)}
      {suffix}
    </>
  )
}
