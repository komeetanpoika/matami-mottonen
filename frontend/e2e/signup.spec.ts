import { expect, test } from '@playwright/test'

const event = {
  id: 1, slug: 'sound-bowl-abcd', title_fi: 'Äänimaljailta', title_en: 'Sound Bowl Evening',
  description_fi: null, description_en: 'Bring a blanket.', starts_at: '2030-10-10T15:00:00Z', ends_at: null,
  location: 'The moss', price_cents: 2500, currency: 'EUR', capacity: 8, seats_left: 3, sold_out: false,
}

test('visitor signs up and is sent to checkout', async ({ page }) => {
  await page.route('**/api/events', r => r.fulfill({ json: [event] }))
  await page.route('**/api/events/sound-bowl-abcd', r => r.fulfill({ json: event }))
  let posted: unknown = null
  await page.route('**/api/events/sound-bowl-abcd/checkout', async r => {
    posted = r.request().postDataJSON()
    await r.fulfill({ json: { registration_id: 'reg-1', checkout_url: 'http://localhost:5173/events/thanks?reg=reg-1' } })
  })
  await page.route('**/api/registrations/reg-1/status', r =>
    r.fulfill({ json: { status: 'confirmed', event_slug: 'sound-bowl-abcd', quantity: 2 } }))

  await page.goto('/events')
  await page.getByText('Sound Bowl Evening').click()
  await expect(page).toHaveURL(/\/events\/sound-bowl-abcd$/)
  await expect(page.getByText('3 seats left')).toBeVisible()
  await page.getByLabel('Name').fill('Aino')
  await page.getByLabel('Email').fill('aino@example.fi')
  await page.getByLabel('Seats').selectOption('2')
  await page.getByRole('button', { name: 'Continue to payment' }).click()

  await expect(page).toHaveURL(/\/events\/thanks\?reg=reg-1/)
  expect(posted).toEqual({ name: 'Aino', email: 'aino@example.fi', quantity: 2, lang: 'en' })
  await expect(page.getByTestId('thanks-status')).toHaveText("You're in. A confirmation is on its way to your email.")
})

test('sold out hides the form', async ({ page }) => {
  await page.route('**/api/events/sound-bowl-abcd', r => r.fulfill({ json: { ...event, seats_left: 0, sold_out: true } }))
  await page.goto('/events/sound-bowl-abcd')
  await expect(page.getByText('Sold out')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Continue to payment' })).toHaveCount(0)
})
