import { describe, expect, it } from 'vitest'

import { pageTitle } from '../title'

describe('pageTitle', () => {
  it('adds the app name', () => {
    expect(pageTitle({ meta: { title: 'Invoices' } })).toBe('Invoices · Timesheets')
    expect(pageTitle({ meta: {} })).toBe('Timesheets')
  })
})
