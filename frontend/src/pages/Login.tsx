import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Leaf, LogIn } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'
import { FieldGroup, Input } from '@/components/ui/Field'
import { LanguageDropdown } from '@/components/LanguageDropdown'
import { ThemeToggle } from '@/components/ThemeToggle'
import { apiErrorMessage } from '@/lib/api'

export default function Login() {
  const { t } = useTranslation()
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
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
          <h1 className="text-lg font-bold text-[var(--text-primary)]">{t('auth.login_title')}</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('auth.login_subtitle')}</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <FieldGroup label={t('auth.email')}>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </FieldGroup>
          <FieldGroup label={t('auth.password')}>
            <Input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </FieldGroup>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <Button type="submit" className="w-full" isLoading={loading}>
            <LogIn size={16} aria-hidden="true" />
            {loading ? t('auth.logging_in') : t('auth.login_button')}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
          {t('auth.no_account')}{' '}
          <Link to="/register" className="font-semibold text-brand-700 hover:underline">
            {t('auth.sign_up_link')}
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
