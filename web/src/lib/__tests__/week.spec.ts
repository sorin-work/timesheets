import { describe, expect, it } from 'vitest'

import { isoDate } from '../format'
import { addDays, mondayOf, weekLabel } from '../week'

describe('mondayOf', () => {
  it('returns the same day for a Monday', () => {
    expect(isoDate(mondayOf(new Date(2026, 1, 9)))).toBe('2026-02-09')
  })

  it('goes back to Monday from a Sunday', () => {
    expect(isoDate(mondayOf(new Date(2026, 1, 15, 23, 30)))).toBe('2026-02-09')
  })
})

describe('addDays', () => {
  it('crosses month and year boundaries', () => {
    expect(addDays('2026-01-29', 7)).toBe('2026-02-05')
    expect(addDays('2026-01-01', -1)).toBe('2025-12-31')
  })
})

describe('weekLabel', () => {
  it('shows the first and last day', () => {
    expect(weekLabel('2026-02-09')).toBe('9 Feb – 15 Feb 2026')
  })
})
