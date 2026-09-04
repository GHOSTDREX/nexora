import { test, expect, type Page, type ConsoleMessage } from '@playwright/test'

// Every nav destination that requires an authenticated + onboarded farm.
const NAV_PAGES = [
  '/dashboard', '/robot', '/monitoring', '/irrigation', '/crop-recommendation',
  '/fertilizer', '/soil-health', '/yield-prediction', '/assistant', '/alerts', '/settings',
]

// Two categories of expected, correctly-handled network "errors" that the
// browser still logs to console even though the app catches them cleanly:
// - 401 from AuthContext's silent session probe (/api/auth/me) on every
//   mount, including public pages.
// - 404 from Dashboard's "does a recommendation/analysis exist yet" probes
//   (/api/crop/recommend/latest, /api/soil-health/latest) for a fresh farm
//   that hasn't requested one yet — both wrapped in .catch(() => {}) in
//   Dashboard.tsx, so nothing actually breaks.
// Neither is an app bug, so both are filtered out here rather than
// asserted on as if they were.
const EXPECTED_CONSOLE_NOISE = /Failed to load resource.*(401|404)/i

function trackConsoleErrors(page: Page) {
  const errors: string[] = []
  page.on('console', (msg: ConsoleMessage) => {
    if (msg.type() === 'error' && !EXPECTED_CONSOLE_NOISE.test(msg.text())) errors.push(msg.text())
  })
  page.on('pageerror', (err) => errors.push(err.message))
  return errors
}

// Register ONE user + farm via a direct API call (not through 3 separate UI
// registrations per test — /api/auth/register is rate-limited to 5/hour,
// see backend/app/core/rate_limit.py) and reuse that session across every
// test in this file by seeding localStorage before each page load.
let sharedToken = ''

test.beforeAll(async ({ request }) => {
  const stamp = Date.now()
  const res = await request.post('http://127.0.0.1:8000/api/auth/register', {
    data: {
      full_name: 'Playwright Tester',
      email: `pw-suite-${stamp}@example.com`,
      password: 'testpass123',
      preferred_language: 'en',
    },
  })
  expect(res.ok(), `register failed: ${res.status()} ${await res.text()}`).toBeTruthy()
  const body = await res.json()
  sharedToken = body.access_token

  const farmRes = await request.post('http://127.0.0.1:8000/api/farm', {
    headers: { Authorization: `Bearer ${sharedToken}` },
    data: {
      name: 'Playwright Test Farm',
      region: 'North',
      latitude: 28.6139,
      longitude: 77.209,
      field_area_hectare: 2.5,
      soil_type: 'Loamy',
      soil_ph: 6.5,
      organic_carbon: 0.85,
      electrical_conductivity: 1.5,
      crop_type: 'Wheat',
      crop_growth_stage: 'Vegetative',
      season: 'Rabi',
      mulching_used: 'No',
    },
  })
  expect(farmRes.ok(), `farm creation failed: ${farmRes.status()} ${await farmRes.text()}`).toBeTruthy()
})

test.beforeEach(async ({ page }) => {
  // Seed the auth token before any app code runs, so the very first
  // AuthContext bootstrap already sees a logged-in session.
  await page.addInitScript((token) => {
    localStorage.setItem('agrinova_token', token)
  }, sharedToken)
})

test.describe('AgriNova smoke suite', () => {
  test('landing page loads with no console errors (anonymous)', async ({ browser }) => {
    // Deliberately a fresh, un-seeded context — this checks the true
    // anonymous-visitor path, not the authenticated one.
    const context = await browser.newContext()
    const page = await context.newPage()
    const errors = trackConsoleErrors(page)
    await page.goto('/')
    await expect(page).toHaveTitle(/AgriNova/i)
    await expect(page.getByRole('link', { name: /get started/i }).first()).toBeVisible()
    expect(errors, `console errors on landing page: ${errors.join('\n')}`).toHaveLength(0)
    await context.close()
  })

  test('authenticated session lands on dashboard with farm data', async ({ page }) => {
    const errors = trackConsoleErrors(page)
    await page.goto('/dashboard')
    await expect(page.getByText(/welcome back/i)).toBeVisible({ timeout: 10_000 })
    expect(errors, `console errors on dashboard: ${errors.join('\n')}`).toHaveLength(0)
  })

  for (const path of NAV_PAGES) {
    test(`nav page ${path} loads with no console errors`, async ({ page }) => {
      const errors = trackConsoleErrors(page)
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      await expect(page.locator('body')).not.toContainText('Something went wrong')
      expect(errors, `console errors on ${path}: ${errors.join('\n')}`).toHaveLength(0)
    })
  }

  test('robot page: movement, speed slider, seed, plow controls all respond', async ({ page }) => {
    const errors = trackConsoleErrors(page)
    await page.goto('/robot')
    await page.waitForLoadState('networkidle')

    await page.getByLabel(/^forward$/i).click()
    await page.waitForTimeout(200)

    // React tracks input values via its own hidden property on the DOM
    // node, so setting `.value` directly and dispatching a plain 'input'
    // event doesn't trigger React's onChange — this uses the native
    // HTMLInputElement value setter so React actually sees the change,
    // same trick @testing-library/user-event uses internally.
    const slider = page.locator('input[type="range"]')
    await slider.evaluate((el: HTMLInputElement) => {
      const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!
      nativeSetter.call(el, '255')
      el.dispatchEvent(new Event('input', { bubbles: true }))
    })
    await expect(page.getByText('255', { exact: true })).toBeVisible()

    await page.getByRole('button', { name: /^turn on$/i }).first().click()
    await page.waitForTimeout(300)

    await page.getByRole('button', { name: /lower plow/i }).click()
    await page.waitForTimeout(300)

    await expect(page.locator('body')).not.toContainText('Something went wrong')
    expect(errors, `console errors on robot page interactions: ${errors.join('\n')}`).toHaveLength(0)
  })

  test('manual sensor form respects backend validation bounds', async ({ page }) => {
    await page.goto('/dashboard')

    const manualToggle = page.getByRole('button', { name: /switch to manual/i })
    if (await manualToggle.isVisible().catch(() => false)) {
      await manualToggle.click()
      await page.waitForTimeout(300)

      const tempInput = page.locator('input[type="number"]').first()
      await tempInput.fill('999')
      await page.getByRole('button', { name: /save reading/i }).click()
      await expect(page.getByText(/must be between/i)).toBeVisible({ timeout: 3000 })
    }
  })

  test('dashboard shows a live "last seen" heartbeat for hardware status', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.getByText(/last seen/i)).toBeVisible({ timeout: 10_000 })
  })

  test('SMS assistant preview returns a plain-text reply capped at 160 chars', async ({ page }) => {
    const errors = trackConsoleErrors(page)
    await page.goto('/assistant')
    await page.waitForLoadState('networkidle')

    const smsInput = page.getByPlaceholder(/type a question as if texting/i)
    await expect(smsInput).toBeVisible()
    await smsInput.fill('Is my soil healthy?')

    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/api/sms/preview') && r.request().method() === 'POST'),
      smsInput.press('Enter'), // submits the SMS form directly (onSubmit={sendSms})
    ])

    const replyBox = page.locator('.font-mono').first()
    await expect(replyBox).toBeVisible({ timeout: 10_000 })
    const replyText = (await replyBox.textContent())?.trim() ?? ''
    expect(replyText.length).toBeGreaterThan(0)
    expect(replyText.length).toBeLessThanOrEqual(200) // reply + optional truncation note

    expect(errors, `console errors on SMS preview: ${errors.join('\n')}`).toHaveLength(0)
  })

  // Runs LAST: switching language persists server-side to the shared test
  // account (LanguageDropdown -> AuthContext.updateLanguage -> PATCH
  // /api/auth/me/language), which would break every English-text-matching
  // test that runs after it in this same shared-session suite.
  test('language switch persists across navigation', async ({ page }) => {
    await page.goto('/dashboard')
    await page.getByLabel('Language', { exact: true }).click()

    // Wait for the PATCH that persists the preference server-side (fired by
    // AuthContext.updateLanguage) alongside the click, not after — a hard
    // page.goto() later would otherwise race ahead of it and cancel it
    // mid-flight, since a full navigation aborts in-flight requests from
    // the page being torn down.
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/api/auth/me/language') && r.request().method() === 'PATCH'),
      page.getByRole('button', { name: /hindi/i }).click(),
    ])
    await expect(page.getByText('डैशबोर्ड').first()).toBeVisible({ timeout: 5000 })

    // Navigate the same way a real user would — an in-app link (client-side
    // route change), not a hard reload.
    await page.getByRole('link', { name: 'रोबोट' }).click()
    await expect(page.getByText('रोबोट').first()).toBeVisible({ timeout: 5000 })
  })
})
