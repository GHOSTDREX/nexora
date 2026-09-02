import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  Leaf,
  Sprout,
  Droplets,
  Bot,
  MessageCircle,
  Bell,
  Wheat,
  Languages,
  ArrowRight,
  ClipboardList,
  Radio,
  Sparkles,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { LanguageDropdown } from '@/components/LanguageDropdown'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/Button'
import { revealOnScroll } from '@/lib/motion'

const featureTone = {
  brand: 'bg-brand-100 text-brand-700',
  gold: 'bg-gold-100 text-gold-700',
  water: 'bg-water-100 text-water-700',
  amber: 'bg-amber-100 text-amber-700',
} as const

const featureDefs = [
  { icon: Sprout, tone: 'brand', key: 'monitoring' },
  { icon: Wheat, tone: 'gold', key: 'crop' },
  { icon: Droplets, tone: 'water', key: 'irrigation' },
  { icon: Bot, tone: 'amber', key: 'robot' },
  { icon: MessageCircle, tone: 'brand', key: 'assistant' },
  { icon: Bell, tone: 'amber', key: 'alerts' },
  { icon: Languages, tone: 'gold', key: 'languages' },
] satisfies { icon: typeof Sprout; tone: keyof typeof featureTone; key: string }[]

const stepDefs = [
  { icon: ClipboardList, key: 'step1' },
  { icon: Radio, key: 'step2' },
  { icon: Sparkles, key: 'step3' },
]

export default function Landing() {
  const { t } = useTranslation()
  const { user, farm, loading } = useAuth()
  const signedIn = !loading && user && farm

  const features = featureDefs.map((f) => ({
    ...f,
    title: t(`landing.feature_${f.key}_title`),
    body: t(`landing.feature_${f.key}_body`),
  }))
  const steps = stepDefs.map((s) => ({
    ...s,
    title: t(`landing.${s.key}_title`),
    body: t(`landing.${s.key}_body`),
  }))
  const stats = [
    { value: '10', label: t('landing.stats_languages') },
    { value: '22', label: t('landing.stats_crops') },
    { value: '24/7', label: t('landing.stats_monitoring') },
  ]

  return (
    <div className="field-grid min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)]">
      <header className="sticky top-0 z-40 border-b border-[var(--border-subtle)] bg-[var(--bg-app)]/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500 text-brand-900">
              <Leaf size={18} aria-hidden="true" />
            </div>
            <div>
              <p className="font-heading text-sm font-bold leading-tight">{t('app_name')}</p>
              <p className="hidden text-[11px] leading-tight text-[var(--text-secondary)] sm:block">{t('tagline')}</p>
            </div>
          </div>

          <nav className="hidden items-center gap-6 text-sm font-medium text-[var(--text-secondary)] md:flex">
            <a href="#features" className="transition-colors hover:text-[var(--text-primary)]">
              {t('landing.nav_features')}
            </a>
            <a href="#how-it-works" className="transition-colors hover:text-[var(--text-primary)]">
              {t('landing.nav_how_it_works')}
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <ThemeToggle compact />
            <LanguageDropdown compact />
            {signedIn ? (
              <Link to="/dashboard">
                <Button size="sm">
                  {t('landing.go_to_dashboard')}
                  <ArrowRight size={14} aria-hidden="true" />
                </Button>
              </Link>
            ) : (
              <>
                <Link to="/login" className="hidden sm:block">
                  <Button variant="ghost" size="sm">
                    {t('auth.sign_in_link')}
                  </Button>
                </Link>
                <Link to="/register">
                  <Button size="sm">{t('landing.get_started')}</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden bg-gradient-to-br from-brand-50 via-[var(--bg-app)] to-sky-tint">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-24 -top-32 h-96 w-96 rounded-full bg-gold-300/50 blur-3xl"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-water-300/40 blur-3xl"
          />
          <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-2 lg:py-28">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            >
              <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-1 text-xs font-medium text-brand-700">
                <Sparkles size={12} aria-hidden="true" />
                {t('landing.hero_badge')}
              </span>
              <h1 className="mt-4 text-3xl font-bold leading-tight sm:text-4xl lg:text-5xl">
                {t('landing.hero_title_1')}
                <br />
                <span className="text-brand-600">{t('landing.hero_title_2')}</span>
              </h1>
              <p className="mt-5 max-w-lg text-base text-[var(--text-secondary)] sm:text-lg">
                {t('landing.hero_subtitle')}
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link to="/register">
                  <Button size="lg">
                    {t('landing.get_started_free')}
                    <ArrowRight size={16} aria-hidden="true" />
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="secondary" size="lg">
                    {t('auth.sign_in_link')}
                  </Button>
                </Link>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.55, ease: 'easeOut', delay: 0.1 }}
              className="relative"
            >
              <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4 shadow-xl shadow-brand-900/10 sm:p-6">
                <div className="mb-4 flex items-center justify-between">
                  <p className="font-heading text-sm font-semibold">{t('landing.mock_overview_title')}</p>
                  <span className="flex items-center gap-1.5 rounded-full bg-brand-100 px-2.5 py-1 text-xs font-medium text-brand-700">
                    <span className="live-pulse h-1.5 w-1.5 rounded-full bg-brand-600" aria-hidden="true" />
                    {t('common.live')}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: t('sensors.soil_moisture'), value: '62%', tone: 'text-brand-700', bg: 'bg-brand-50' },
                    { label: t('sensors.temperature'), value: '29°C', tone: 'text-gold-700', bg: 'bg-gold-50' },
                    { label: t('sensors.humidity'), value: '58%', tone: 'text-water-700', bg: 'bg-water-50' },
                    { label: t('irrigation.prediction'), value: t('irrigation.low'), tone: 'text-brand-700', bg: 'bg-brand-50' },
                  ].map((s) => (
                    <div key={s.label} className={`rounded-xl ${s.bg} p-3`}>
                      <p className="text-[11px] text-[var(--text-secondary)]">{s.label}</p>
                      <p className={`mt-1 font-heading text-lg font-bold ${s.tone}`}>{s.value}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-3 rounded-xl border border-dashed border-[var(--border-subtle)] p-3">
                  <p className="text-[11px] font-medium text-[var(--text-secondary)]">{t('crop.recommended_crop')}</p>
                  <p className="mt-0.5 font-heading text-sm font-bold text-brand-700">{t('landing.mock_crop_value')}</p>
                </div>
              </div>
              <div
                className="absolute -bottom-4 -left-4 hidden h-24 w-24 rounded-2xl bg-gold-100 sm:block"
                style={{ zIndex: -1 }}
                aria-hidden="true"
              />
            </motion.div>
          </div>
        </section>

        <section className="border-y border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <div className="mx-auto grid max-w-6xl grid-cols-1 gap-4 divide-x-0 px-4 py-8 sm:grid-cols-3 sm:gap-0 sm:divide-x sm:divide-[var(--border-subtle)] sm:px-6">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <p className="font-heading text-2xl font-bold text-brand-600 sm:text-3xl">{s.value}</p>
                <p className="mt-1 text-xs text-[var(--text-secondary)] sm:text-sm">{s.label}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.4 }}
            variants={revealOnScroll}
            className="mx-auto max-w-2xl text-center"
          >
            <h2 className="text-2xl font-bold sm:text-3xl">{t('landing.features_title')}</h2>
            <p className="mt-3 text-[var(--text-secondary)]">{t('landing.features_subtitle')}</p>
          </motion.div>

          <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.3 }}
                variants={revealOnScroll}
                transition={{ delay: (i % 4) * 0.06 }}
                className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5"
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${featureTone[f.tone]}`}>
                  <f.icon size={20} aria-hidden="true" />
                </div>
                <h3 className="mt-3 font-heading text-sm font-semibold">{f.title}</h3>
                <p className="mt-1.5 text-sm text-[var(--text-secondary)]">{f.body}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <section id="how-it-works" className="border-t border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
            <motion.div
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.4 }}
              variants={revealOnScroll}
              className="mx-auto max-w-2xl text-center"
            >
              <h2 className="text-2xl font-bold sm:text-3xl">{t('landing.how_title')}</h2>
            </motion.div>

            <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-3">
              {steps.map((s, i) => (
                <motion.div
                  key={s.key}
                  initial="hidden"
                  whileInView="show"
                  viewport={{ once: true, amount: 0.4 }}
                  variants={revealOnScroll}
                  transition={{ delay: i * 0.08 }}
                  className="relative"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-500 text-brand-900">
                    <s.icon size={20} aria-hidden="true" />
                  </div>
                  <p className="mt-4 text-xs font-semibold text-brand-600">{t('landing.step_label', { n: i + 1 })}</p>
                  <h3 className="mt-1 font-heading text-base font-semibold">{s.title}</h3>
                  <p className="mt-1.5 text-sm text-[var(--text-secondary)]">{s.body}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.4 }}
            variants={revealOnScroll}
            className="relative flex flex-col items-center justify-between gap-6 overflow-hidden rounded-3xl bg-brand-500 px-6 py-10 text-center text-brand-900 sm:px-12 sm:py-14 lg:flex-row lg:text-left"
          >
            <div aria-hidden="true" className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-900/10 blur-3xl" />
            <div aria-hidden="true" className="pointer-events-none absolute -bottom-20 left-1/3 h-56 w-56 rounded-full bg-gold-300/25 blur-3xl" />
            <div className="relative">
              <h2 className="text-2xl font-bold sm:text-3xl">{t('landing.cta_title')}</h2>
              <p className="mt-2 max-w-md text-brand-800">{t('landing.cta_subtitle')}</p>
            </div>
            <Link to="/register" className="shrink-0">
              <Button size="lg" className="!bg-brand-900 !text-brand-400 hover:!bg-black">
                {t('landing.get_started_free')}
                <ArrowRight size={16} aria-hidden="true" />
              </Button>
            </Link>
          </motion.div>
        </section>
      </main>

      <footer className="border-t border-[var(--border-subtle)]">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-[var(--text-secondary)] sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-brand-500 text-brand-900">
              <Leaf size={12} aria-hidden="true" />
            </div>
            <span className="font-heading font-semibold text-[var(--text-primary)]">{t('app_name')}</span>
          </div>
          <p>
            {t('tagline')} {t('landing.footer_suffix')}
          </p>
        </div>
      </footer>
    </div>
  )
}
