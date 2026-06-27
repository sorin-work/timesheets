import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi } from '@/__tests__/helpers'

import ClientForm from '../ClientForm.vue'

afterEach(() => vi.unstubAllGlobals())

describe('ClientForm', () => {
  it('sends empty optional fields as null', async () => {
    const fetch = mockApi({ 'POST /api/clients': { status: 201, body: { id: 1, name: 'Acme' } } })
    const wrapper = mount(ClientForm)
    await wrapper.find('input[maxlength="200"]').setValue('Acme')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    const body = JSON.parse(fetch.mock.calls[0]![1]!.body as string)
    expect(body).toMatchObject({ name: 'Acme', email: null, hourly_rate: null, currency: 'EUR' })
    expect(wrapper.emitted('saved')).toHaveLength(1)
  })

  it('shows field errors from the api next to the fields', async () => {
    mockApi({
      'POST /api/clients': () => ({
        status: 422,
        body: {
          error: {
            code: 'validation_failed',
            message: 'Some fields are invalid',
            details: [
              { field: 'hourly_rate', message: 'Input should be greater than or equal to 0' },
            ],
          },
        },
      }),
    })
    const wrapper = mount(ClientForm)
    await wrapper.find('input[maxlength="200"]').setValue('Acme')
    await wrapper.find('input[inputmode="decimal"]').setValue('-5')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('greater than or equal to 0')
    expect(wrapper.emitted('saved')).toBeUndefined()
  })

  it('patches an existing client', async () => {
    const fetch = mockApi({ 'PATCH /api/clients/4': { id: 4, name: 'Acme Ltd' } })
    const wrapper = mount(ClientForm, {
      props: {
        client: {
          id: 4,
          name: 'Acme',
          email: null,
          address: null,
          currency: 'GBP',
          hourly_rate: '70.00',
          notes: null,
          archived_at: null,
          created_at: '2026-01-01T00:00:00Z',
        },
      },
    })
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(fetch.mock.calls[0]![1]!.method).toBe('PATCH')
    expect(JSON.parse(fetch.mock.calls[0]![1]!.body as string).currency).toBe('GBP')
  })
})
