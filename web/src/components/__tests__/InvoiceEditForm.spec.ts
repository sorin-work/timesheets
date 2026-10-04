import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi } from '@/__tests__/helpers'
import type { Invoice } from '@/api/types'

import InvoiceEditForm from '../InvoiceEditForm.vue'

afterEach(() => vi.unstubAllGlobals())

const invoice = {
  id: 8,
  issue_date: '2026-10-01',
  due_date: '2026-10-15',
  notes: null,
  reference: null,
  taxes: [{ name: 'VAT', rate: '19.00', amount: '19.00' }],
} as unknown as Invoice

describe('InvoiceEditForm', () => {
  it('sends dates, notes and taxes', async () => {
    const fetch = mockApi({ 'PATCH /api/invoices/8': { ...invoice, notes: 'Thanks' } })
    const wrapper = mount(InvoiceEditForm, { props: { invoice } })
    expect((wrapper.find('input[aria-label="Rate %"]').element as HTMLInputElement).value).toBe(
      '19',
    )
    await wrapper.find('textarea').setValue('Thanks')
    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Remove')!
      .trigger('click')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(JSON.parse(fetch.mock.calls[0]![1]!.body as string)).toEqual({
      issue_date: '2026-10-01',
      due_date: '2026-10-15',
      notes: 'Thanks',
      reference: '',
      taxes: [],
    })
    expect(wrapper.emitted('saved')).toHaveLength(1)
  })

  it('shows the validation message', async () => {
    mockApi({
      'PATCH /api/invoices/8': () => ({
        status: 422,
        body: { error: { message: 'The due date cannot be before the issue date' } },
      }),
    })
    const wrapper = mount(InvoiceEditForm, { props: { invoice } })
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('The due date cannot be before the issue date')
  })
})
