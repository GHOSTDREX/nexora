import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Leaf, UserPlus } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'
import { FieldGroup, Input } from '@/components/ui/Field'
import { LanguageDropdown } from '@/components/LanguageDropdown'
import { ThemeToggle } from '@/components/ThemeToggle'
import { apiErrorMessage } from '@/lib/api'

export default function Register() {
  const { t, i18n } = useTranslation()
  const { register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(fullName, email, password, i18n.language)
      navigate('/onboarding')
    } catch (err) {
      setError(apiErrorMessage(err, t('common.error_generic')))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-[var(--bg-app)] to-sky-tint px-4 py-10">
      <div className="absolute right-4 top-4 flex items-center gap-2">
        <ThemeToggle compact />
        <LanguageDropdown />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="w-full max-w-sm rounded-3xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-8 shadow-xl shadow-brand-900/5"
      >
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500 text-brand-900">
            <Leaf size={22} aria-hidden="true" />
          </div>
          <h1 className="text-lg font-bold text-[var(--text-primary)]">{t('auth.register_title')}</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('auth.register_subtitle')}</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <FieldGroup label={t('auth.full_name')}>
            <Input required value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Ramesh Kumar" />
          </FieldGroup>
          <FieldGroup label={t('auth.email')}>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </FieldGroup>
          <FieldGroup label={t('auth.password')}>
            <Input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </FieldGroup>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <Button type="submit" className="w-full" isLoading={loading}>
            <UserPlus size={16} aria-hidden="true" />
            {loading ? t('auth.registering') : t('auth.register_button')}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
          {t('auth.have_account')}{' '}
          <Link to="/login" className="font-semibold text-brand-700 hover:underline">
            {t('auth.sign_in_link')}
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
