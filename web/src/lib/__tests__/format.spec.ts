import { describe, expect, it } from 'vitest'

import {
  formatClock,
  formatDuration,
  formatHours,
  formatMoney,
  isoDate,
  parseDuration,
} from '../format'

describe('formatDuration', () => {
  it('formats hours and minutes', () => {
    expect(formatDuration(0)).toBe('0:00')
    expect(formatDuration(5400)).toBe('1:30')
    expect(formatDuration(59)).toBe('0:00')
    expect(formatDuration(36000 + 300)).toBe('10:05')
  })

  it('keeps the sign of negative values', () => {
    expect(formatDuration(-1800)).toBe('-0:30')
  })
})

describe('formatClock', () => {
  it('shows seconds for the running timer', () => {
    expect(formatClock(5)).toBe('0:00:05')
    expect(formatClock(3725)).toBe('1:02:05')
  })
})

describe('formatHours', () => {
  it('uses two decimals', () => {
    expect(formatHours(5400)).toBe('1.50')
    expect(formatHours(600)).toBe('0.17')
  })
})

describe('parseDuration', () => {
  it.each([
    ['1:30', 90],
    ['0:05', 5],
    ['1.5', 90],
    ['1,25', 75],
    ['90m', 90],
    ['2h', 120],
    ['1h 15m', 75],
    ['1h30', 90],
    ['2h 5', 125],
    ['45', 45],
    ['3', 180],
    ['', 0],
  ])('parses %s as %i minutes', (input, minutes) => {
    expect(parseDuration(input)).toBe(minutes)
  })

  it('rejects garbage', () => {
    expect(parseDuration('abc')).toBeNull()
    expect(parseDuration('1:75')).toBeNull()
    expect(parseDuration('1h75')).toBeNull()
  })
})

describe('formatMoney', () => {
  it('formats with the currency', () => {
    expect(formatMoney('1234.5', 'EUR')).toBe('€1,234.50')
    expect(formatMoney(80, 'USD')).toBe('US$80.00')
  })
})

describe('isoDate', () => {
  it('uses the local calendar date', () => {
    expect(isoDate(new Date(2026, 0, 5, 23, 59))).toBe('2026-01-05')
  })
})
