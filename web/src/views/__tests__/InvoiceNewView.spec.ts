import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi, testRouter } from '@/__tests__/helpers'

import InvoiceNewView from '../InvoiceNewView.vue'

afterEach(() => vi.unstubAllGlobals())

const routes = {
  'GET /api/clients': [{ id: 4, name: 'Acme', currency: 'EUR' }],
  'GET /api/settings': { default_taxes: [{ name: 'VAT', rate: '19' }] },
  'GET /api/invoices/unbilled': {
    client_id: 4,
    currency: 'EUR',
    projects: [
      {
        project_id: 9,
        project_name: 'Website',
        hourly_rate: '100.00',
        entries: 3,
        seconds: 7200,
        billable_seconds: 7200,
      },
    ],
  },
}

async function mountView(generate: () => { status?: number; body?: unknown }) {
  const fetch = mockApi({ ...routes, 'POST /api/invoices/generate': generate })
  const router = testRouter([{ path: '/invoices/:id', component: { template: '<div />' } }])
  await router.push('/')
  const wrapper = mount(InvoiceNewView, { global: { plugins: [router] } })
  await flushPromises()
  return { wrapper, fetch, router }
}

function generateCalls(fetch: ReturnType<typeof mockApi>) {
  return fetch.mock.calls.filter(([url]) => String(url).includes('/invoices/generate'))
}

describe('InvoiceNewView', () => {
  it('prefills default taxes and previews unbilled time', async () => {
    const { wrapper } = await mountView(() => ({ status: 201, body: { id: 1 } }))
    expect(wrapper.text()).toContain('Website')
    expect(wrapper.text()).toContain('€200.00')
    expect((wrapper.find('input[aria-label="Tax name"]').element as HTMLInputElement).value).toBe(
      'VAT',
    )
  })

  it('creates only one invoice when the button is clicked twice', async () => {
    const { wrapper, fetch, router } = await mountView(() => ({ status: 201, body: { id: 12 } }))
    const form = wrapper.find('form')
    await form.trigger('submit')
    await form.trigger('submit')
    await flushPromises()
    expect(generateCalls(fetch)).toHaveLength(1)
    expect(router.currentRoute.value.path).toBe('/invoices/12')
  })

  it('lets you try again after an error', async () => {
    let fail = true
    const { wrapper, fetch } = await mountView(() =>
      fail
        ? { status: 422, body: { error: { message: 'Set an hourly rate first' } } }
        : { status: 201, body: { id: 3 } },
    )
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[role=alert]').text()).toBe('Set an hourly rate first')
    fail = false
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(generateCalls(fetch)).toHaveLength(2)
  })
})
