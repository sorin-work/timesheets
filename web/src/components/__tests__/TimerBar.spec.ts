import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi } from '@/__tests__/helpers'

import TimerBar from '../TimerBar.vue'

afterEach(() => vi.unstubAllGlobals())

const project = { id: 2, name: 'Website', client_name: 'Acme', client_id: 1 }

function running(description: string) {
  return {
    id: 10,
    project_id: 2,
    project_name: 'Website',
    started_at: new Date(Date.now() - 65_000).toISOString(),
    ended_at: null,
    running: true,
    description,
  }
}

describe('TimerBar', () => {
  it('starts a timer for the chosen project', async () => {
    const fetch = mockApi({
      'GET /api/projects': [project],
      'GET /api/timer': () => ({ body: null }),
      'POST /api/timer/start': (_, init) => ({
        status: 201,
        body: running(JSON.parse(init.body as string).description),
      }),
    })
    const wrapper = mount(TimerBar)
    await flushPromises()
    await wrapper.find('select').setValue(2)
    await wrapper.find('input.description').setValue('Hero section')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const start = fetch.mock.calls.find(([url]) => String(url).endsWith('/timer/start'))!
    expect(JSON.parse(start[1]!.body as string)).toEqual({
      project_id: 2,
      description: 'Hero section',
    })
    expect(wrapper.find('button[type=submit]').text()).toBe('Stop')
    expect(wrapper.find('.clock').text()).toMatch(/^0:01:0\d$/)
  })

  it('picks up a timer that is already running', async () => {
    mockApi({ 'GET /api/projects': [project], 'GET /api/timer': running('Already going') })
    const wrapper = mount(TimerBar)
    await flushPromises()
    expect((wrapper.find('input.description').element as HTMLInputElement).value).toBe(
      'Already going',
    )
    expect(wrapper.find('button[type=submit]').text()).toBe('Stop')
  })
})
