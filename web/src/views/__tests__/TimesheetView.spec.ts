import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi, testRouter } from '@/__tests__/helpers'
import type { Timesheet } from '@/api/types'
import { useProjects } from '@/stores/projects'

import TimesheetView from '../TimesheetView.vue'

afterEach(() => vi.unstubAllGlobals())

const days = [
  '2026-06-01',
  '2026-06-02',
  '2026-06-03',
  '2026-06-04',
  '2026-06-05',
  '2026-06-06',
  '2026-06-07',
]

function sheet(seconds: number[]): Timesheet {
  const total = seconds.reduce((a, b) => a + b, 0)
  return {
    week_start: days[0]!,
    days,
    rows: [
      {
        project_id: 3,
        project_name: 'Website',
        client_name: 'Acme',
        color: '#000',
        seconds,
        total,
      },
    ],
    totals: seconds,
    total,
  }
}

async function mountView() {
  const fetch = mockApi({
    'GET /api/projects': [],
    'GET /api/timesheet': sheet([3600, 0, 0, 0, 0, 0, 0]),
    'PUT /api/timesheet/cell': (_, init) => {
      const body = JSON.parse(init.body as string)
      return { body: sheet([3600, body.minutes * 60, 0, 0, 0, 0, 0]) }
    },
  })
  useProjects().load(true)
  const router = testRouter([{ path: '/timesheet', component: TimesheetView }])
  await router.push('/timesheet?week=2026-06-01')
  const wrapper = mount(TimesheetView, { global: { plugins: [router] } })
  await flushPromises()
  return { wrapper, fetch }
}

describe('TimesheetView', () => {
  it('shows the week with totals', async () => {
    const { wrapper, fetch } = await mountView()
    expect(String(fetch.mock.calls.find(([u]) => String(u).includes('timesheet'))![0])).toContain(
      'week=2026-06-01',
    )
    expect(wrapper.text()).toContain('1 Jun – 7 Jun 2026')
    expect(wrapper.text()).toContain('Website')
    expect(wrapper.find('tfoot').text()).toContain('1:00')
  })

  it('saves a cell and shows the new totals', async () => {
    const { wrapper, fetch } = await mountView()
    const tuesday = wrapper.find('input[aria-label="Website, 2026-06-02"]')
    await tuesday.setValue('1:30')
    await tuesday.trigger('blur')
    await flushPromises()

    const put = fetch.mock.calls.find(([, init]) => init?.method === 'PUT')!
    expect(JSON.parse(put[1]!.body as string)).toEqual({
      project_id: 3,
      date: '2026-06-02',
      minutes: 90,
    })
    expect(wrapper.find('tfoot').text()).toContain('2:30')
  })
})
