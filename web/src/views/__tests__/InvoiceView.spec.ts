import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi, testRouter } from '@/__tests__/helpers'

import InvoiceView from '../InvoiceView.vue'

afterEach(() => vi.unstubAllGlobals())

const invoice = {
  id: 5,
  number: 'INV-5',
  client_id: 2,
  client_name: 'Acme <b>Ltd</b>',
  status: 'draft',
  issue_date: '2026-05-01',
  due_date: '2026-05-15',
  currency: 'EUR',
  subtotal: '100.00',
  tax_total: '19.00',
  total: '119.00',
  period_start: '2026-04-01',
  period_end: '2026-04-30',
  notes: 'Thanks!\n<img src=x onerror="window.pwned=1">',
  sent_at: null,
  paid_at: null,
  lines: [
    {
      id: 1,
      project_id: 9,
      description: 'Website',
      quantity: '1.00',
      unit_price: '100.00',
      amount: '100.00',
    },
  ],
  taxes: [{ name: 'VAT', rate: '19.00', amount: '19.00' }],
  entry_count: 2,
}

async function mountView() {
  mockApi({
    'GET /api/invoices/5': invoice,
    'GET /api/clients/2': { id: 2, name: 'Acme', address: '1 Road\nTown', email: null },
    'GET /api/settings': { name: 'Fran', business_name: 'Fran Dev', business_address: null },
  })
  const router = testRouter([{ path: '/invoices/:id', component: InvoiceView }])
  await router.push('/invoices/5')
  const wrapper = mount(InvoiceView, { global: { plugins: [router] } })
  await flushPromises()
  return wrapper
}

describe('InvoiceView', () => {
  it('shows lines, taxes and totals', async () => {
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('Invoice INV-5')
    expect(wrapper.text()).toContain('VAT (19%)')
    expect(wrapper.text()).toContain('€119.00')
  })

  it('renders notes and names as text, not html', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('.notes img').exists()).toBe(false)
    expect(wrapper.find('.notes').text()).toContain('<img src=x')
    expect(wrapper.find('.paper b').exists()).toBe(false)
  })
})
