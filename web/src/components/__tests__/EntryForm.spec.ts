import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { flush, mockApi } from '@/__tests__/helpers'
import type { Entry, Project } from '@/api/types'
import { useProjects } from '@/stores/projects'

import EntryForm from '../EntryForm.vue'

const project: Project = {
  id: 7,
  client_id: 1,
  client_name: 'Acme',
  name: 'Website',
  hourly_rate: null,
  effective_rate: '80.00',
  currency: 'EUR',
  billable: true,
  color: '#4f46e5',
  archived_at: null,
  created_at: '2026-01-01T00:00:00Z',
}

function entry(overrides: Partial<Entry> = {}): Entry {
  return {
    id: 3,
    project_id: 7,
    project_name: 'Website',
    client_id: 1,
    client_name: 'Acme',
    started_at: new Date(2026, 2, 10, 9, 0).toISOString(),
    ended_at: new Date(2026, 2, 10, 10, 30).toISOString(),
    duration_seconds: 5400,
    running: false,
    description: 'Header',
    billable: true,
    source: 'manual',
    invoice_id: null,
    hourly_rate: '80.00',
    ...overrides,
  }
}

beforeEach(() => {
  useProjects().projects.value = [project]
})

afterEach(() => vi.unstubAllGlobals())

describe('EntryForm', () => {
  it('creates an entry from the date and times', async () => {
    const fetch = mockApi({ 'POST /api/entries': (_, init) => ({ status: 201, body: init.body }) })
    const wrapper = mount(EntryForm, { props: { defaultDate: '2026-03-10' } })
    const [, start, end] = wrapper.findAll('input[type=date], input[type=time]')
    await start!.setValue('13:15')
    await end!.setValue('14:00')
    expect(wrapper.text()).toContain('Duration: 0:45')
    await wrapper.find('form').trigger('submit')
    await flush()

    const body = JSON.parse(fetch.mock.calls[0]![1]!.body as string)
    expect(body.project_id).toBe(7)
    expect(new Date(body.started_at)).toEqual(new Date(2026, 2, 10, 13, 15))
    expect(new Date(body.ended_at)).toEqual(new Date(2026, 2, 10, 14, 0))
    expect(wrapper.emitted('saved')).toHaveLength(1)
  })

  it('treats an end time before the start as the next day', async () => {
    mockApi({})
    const wrapper = mount(EntryForm, { props: { defaultDate: '2026-03-10' } })
    const [, start, end] = wrapper.findAll('input[type=date], input[type=time]')
    await start!.setValue('22:00')
    await end!.setValue('01:30')
    expect(wrapper.text()).toContain('Duration: 3:30')
  })

  it('only sends the fields that changed when editing', async () => {
    const fetch = mockApi({ 'PATCH /api/entries/3': { ...entry(), description: 'Footer' } })
    const wrapper = mount(EntryForm, { props: { entry: entry() } })
    await wrapper.find('input[maxlength="500"]').setValue('Footer')
    await wrapper.find('form').trigger('submit')
    await flush()
    expect(JSON.parse(fetch.mock.calls[0]![1]!.body as string)).toEqual({ description: 'Footer' })
  })

  it('is read-only for invoiced entries', () => {
    const wrapper = mount(EntryForm, { props: { entry: entry({ invoice_id: 12 }) } })
    expect(wrapper.text()).toContain('on an invoice')
    expect(wrapper.find('fieldset').attributes('disabled')).toBeDefined()
    expect(wrapper.find('button[type=submit]').exists()).toBe(false)
  })
})
