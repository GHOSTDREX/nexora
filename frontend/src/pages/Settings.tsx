import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Save, User, Sprout, Cpu } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { api, apiErrorMessage } from '@/lib/api'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { FieldGroup, Input, Select } from '@/components/ui/Field'
import { LanguageDropdown } from '@/components/LanguageDropdown'
import { IconBadge } from '@/components/ui/IconBadge'
import { REGIONS, SOIL_TYPES, CROP_TYPES, GROWTH_STAGES, SEASONS } from '@/lib/farmOptions'
import type { Farm } from '@/lib/types'

export default function Settings() {
  const { t } = useTranslation()
  const { user, farm, setFarm } = useAuth()
  const [form, setForm] = useState<Farm | null>(farm)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => setForm(farm), [farm])

  function update<K extends keyof Farm>(key: K, value: Farm[K]) {
    setForm((f) => (f ? { ...f, [key]: value } : f))
  }

  async function save(e: React.FormEvent) {
    e.preventDefault()
    if (!form) return
    setSaving(true)
    setMessage('')
    try {
      const { data } = await api.put<Farm>('/api/farm', form)
      setFarm(data)
      setMessage(t('settings.save_success'))
    } catch (err) {
      setMessage(apiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (!form) return null

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('settings.title')}</h1>

      <Card>
        <CardHeader title={t('settings.profile')} action={<IconBadge icon={<User size={16} aria-hidden="true" />} tone="brand" />} />
        <div className="grid grid-cols-1 gap-4 px-5 pb-5 pt-3 sm:grid-cols-2">
          <FieldGroup label={t('auth.full_name')}>
            <Input value={user?.full_name ?? ''} disabled />
          </FieldGroup>
          <FieldGroup label={t('auth.email')}>
            <Input value={user?.email ?? ''} disabled />
          </FieldGroup>
          <FieldGroup label={t('settings.language')}>
            <LanguageDropdown />
          </FieldGroup>
        </div>
      </Card>

      <Card>
        <CardHeader title={t('settings.farm_settings')} action={<IconBadge icon={<Sprout size={16} aria-hidden="true" />} tone="gold" />} />
        <form onSubmit={save} className="grid grid-cols-1 gap-4 px-5 pb-5 pt-3 sm:grid-cols-2">
          <FieldGroup label={t('onboarding.farm_name')}>
            <Input required value={form.name} onChange={(e) => update('name', e.target.value)} />
          </FieldGroup>

          <FieldGroup label={t('onboarding.region')}>
            <Select value={form.region} onChange={(e) => update('region', e.target.value)}>
              {REGIONS.map((r) => (
                <option key={r} value={r}>{t(`options.region.${r}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.field_area')}>
            <Input type="number" step="any" min="0.01" value={form.field_area_hectare} onChange={(e) => update('field_area_hectare', Number(e.target.value))} />
          </FieldGroup>

          <FieldGroup label={t('onboarding.soil_type')}>
            <Select value={form.soil_type} onChange={(e) => update('soil_type', e.target.value)}>
              {SOIL_TYPES.map((s) => (
                <option key={s} value={s}>{t(`options.soil_type.${s}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.soil_ph')}>
            <Input type="number" step="any" min="3.5" max="10.5" value={form.soil_ph} onChange={(e) => update('soil_ph', Number(e.target.value))} />
          </FieldGroup>

          <FieldGroup label={t('onboarding.organic_carbon')}>
            <Input type="number" step="any" value={form.organic_carbon} onChange={(e) => update('organic_carbon', Number(e.target.value))} />
          </FieldGroup>

          <FieldGroup label={t('onboarding.crop_type')}>
            <Select value={form.crop_type} onChange={(e) => update('crop_type', e.target.value)}>
              {CROP_TYPES.map((c) => (
                <option key={c} value={c}>{t(`options.crop_type.${c}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.crop_growth_stage')}>
            <Select value={form.crop_growth_stage} onChange={(e) => update('crop_growth_stage', e.target.value)}>
              {GROWTH_STAGES.map((g) => (
                <option key={g} value={g}>{t(`options.growth_stage.${g}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.season')}>
            <Select value={form.season} onChange={(e) => update('season', e.target.value)}>
              {SEASONS.map((s) => (
                <option key={s} value={s}>{t(`options.season.${s}`)}</option>
              ))}
            </Select>
          </FieldGroup>

          <FieldGroup label={t('onboarding.mulching_used')}>
            <Select value={form.mulching_used} onChange={(e) => update('mulching_used', e.target.value)}>
              <option value="Yes">{t('common.yes')}</option>
              <option value="No">{t('common.no')}</option>
            </Select>
          </FieldGroup>

          {message && <p className="text-sm text-brand-700 sm:col-span-2">{message}</p>}

          <Button type="submit" className="sm:col-span-2" isLoading={saving}>
            <Save size={15} aria-hidden="true" /> {t('common.save')}
          </Button>
        </form>
      </Card>

      <Card>
        <CardHeader title={t('settings.hardware_settings')} action={<IconBadge icon={<Cpu size={16} aria-hidden="true" />} tone="water" />} />
        <form onSubmit={save} className="grid grid-cols-1 gap-4 px-5 pb-5 pt-3 sm:grid-cols-2">
          <p className="text-xs text-[var(--text-secondary)] sm:col-span-2">{t('settings.hardware_hint')}</p>

          <FieldGroup label={t('settings.hardware_enabled')}>
            <Select value={form.hardware_enabled ? 'Yes' : 'No'} onChange={(e) => update('hardware_enabled', e.target.value === 'Yes')}>
              <option value="Yes">{t('common.yes')}</option>
              <option value="No">{t('common.no')}</option>
            </Select>
          </FieldGroup>

          <div />

          <FieldGroup label={t('settings.sensor_node_host')}>
            <Input placeholder={t('settings.hardware_host_placeholder')} value={form.sensor_node_host} onChange={(e) => update('sensor_node_host', e.target.value)} />
          </FieldGroup>

          <FieldGroup label={t('settings.robot_host')}>
            <Input placeholder={t('settings.hardware_host_placeholder')} value={form.robot_host} onChange={(e) => update('robot_host', e.target.value)} />
          </FieldGroup>

          <FieldGroup label={t('settings.camera_host')}>
            <Input placeholder={t('settings.hardware_host_placeholder')} value={form.camera_host} onChange={(e) => update('camera_host', e.target.value)} />
          </FieldGroup>

          <Button type="submit" className="sm:col-span-2" isLoading={saving}>
            <Save size={15} aria-hidden="true" /> {t('common.save')}
          </Button>
        </form>
      </Card>
    </div>
  )
}
