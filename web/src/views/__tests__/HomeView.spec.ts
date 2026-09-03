import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi } from '@/__tests__/helpers'

import HomeView from '../HomeView.vue'

afterEach(() => vi.unstubAllGlobals())

describe('HomeView', () => {
  it('shows the numbers and budget warnings', async () => {
    mockApi({
      'GET /api/dashboard': {
        today_seconds: 3600,
        week_seconds: 5 * 3600,
        unbilled_seconds: 7200,
        unbilled: [{ currency: 'EUR', amount: '200.00' }],
        outstanding: [],
        outstanding_count: 0,
        overdue_count: 0,
        recent: [],
        budgets: [
          {
            project_id: 1,
            project_name: 'Website',
            client_name: 'Acme',
            budget_hours: '10.00',
            used_seconds: 9 * 3600,
            percent: 90,
          },
        ],
      },
    })
    const wrapper = mount(HomeView, {
      global: { stubs: { RouterLink: RouterLinkStub, GettingStarted: true } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('5:00')
    expect(wrapper.text()).toContain('€200.00')
    expect(wrapper.text()).toContain('Acme · Website')
    expect(wrapper.text()).toContain('90%')
    expect(wrapper.text()).toContain('Nothing tracked yet')
  })
})
