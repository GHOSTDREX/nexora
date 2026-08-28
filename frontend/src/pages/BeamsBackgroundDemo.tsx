import HolographicBeams from '@/components/ui/beams-background'

export default function BeamsBackgroundDemo() {
  return (
    <div className="relative flex h-screen w-full items-center justify-center overflow-hidden bg-black font-sans">
      <HolographicBeams density={15} speed={1.5} aberration={3} opacity={90} />

      <h1 className="relative z-30 -translate-y-8 select-none px-4 text-center text-5xl font-semibold tracking-tight text-transparent drop-shadow-[0_0_35px_rgba(255,255,255,0.25)] sm:text-7xl md:text-8xl lg:text-9xl bg-gradient-to-b from-white via-white/90 to-white/30 bg-clip-text">
        Calmness in design
      </h1>
    </div>
  )
}
