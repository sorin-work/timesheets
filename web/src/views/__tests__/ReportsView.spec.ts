import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi } from '@/__tests__/helpers'

import ReportsView from '../ReportsView.vue'

afterEach(() => vi.unstubAllGlobals())

const months = Array.from({ length: 12 }, (_, i) => ({
  month: `2026-${String(i + 1).padStart(2, '0')}`,
  invoiced: i === 2 ? [{ currency: 'EUR', amount: '1200.00' }] : [],
  paid: i === 3 ? [{ currency: 'EUR', amount: '1200.00' }] : [],
}))

describe('ReportsView', () => {
  it('shows totals and rows, and regroups on change', async () => {
    const fetch = mockApi({
      'GET /api/clients': [],
      'GET /api/reports/time': (url) => ({
        body: {
          group_by: new URL(url, 'http://x').searchParams.get('group_by'),
          rows: [
            {
              key: '1',
              label: 'Acme',
              tracked_seconds: 7200,
              billable_seconds: 5400,
              unbilled_seconds: 1800,
              amounts: [{ currency: 'EUR', amount: '150.00' }],
            },
          ],
          tracked_seconds: 7200,
          billable_seconds: 5400,
          amounts: [{ currency: 'EUR', amount: '150.00' }],
        },
      }),
      'GET /api/reports/revenue': {
        year: 2026,
        months,
        invoiced: [{ currency: 'EUR', amount: '1200.00' }],
        paid: [{ currency: 'EUR', amount: '1200.00' }],
      },
    })
    const wrapper = mount(ReportsView, { global: { stubs: { RouterLink: true } } })
    await flushPromises()
    expect(wrapper.text()).toContain('2:00')
    expect(wrapper.text()).toContain('Acme')
    expect(wrapper.text()).toContain('€150.00')
    expect(wrapper.find('svg[role=img]').exists()).toBe(true)

    await wrapper.find('select[aria-label="Group by"]').setValue('month')
    await flushPromises()
    const last = fetch.mock.calls.filter(([u]) => String(u).includes('/reports/time')).at(-1)!
    expect(String(last[0])).toContain('group_by=month')
  })
})
