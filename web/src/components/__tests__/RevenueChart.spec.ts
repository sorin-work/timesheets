import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { RevenueReport } from '@/api/types'

import RevenueChart from '../RevenueChart.vue'
import StatusBadge from '../StatusBadge.vue'

function report(invoicedInMarch: string): RevenueReport {
  return {
    year: 2026,
    months: Array.from({ length: 12 }, (_, i) => ({
      month: `2026-${String(i + 1).padStart(2, '0')}`,
      invoiced: i === 2 ? [{ currency: 'EUR', amount: invoicedInMarch }] : [],
      paid: [],
    })),
    invoiced: [],
    paid: [],
  }
}

describe('RevenueChart', () => {
  it('draws a bar per month scaled to the largest value', () => {
    const wrapper = mount(RevenueChart, { props: { report: report('500.00'), currency: 'EUR' } })
    const bars = wrapper.findAll('rect.invoiced')
    expect(bars).toHaveLength(12)
    expect(Number(bars[2]!.attributes('height'))).toBeGreaterThan(100)
    expect(Number(bars[0]!.attributes('height'))).toBe(0)
  })

  it('ignores other currencies and says so when empty', () => {
    const wrapper = mount(RevenueChart, { props: { report: report('500.00'), currency: 'USD' } })
    expect(wrapper.text()).toContain('No invoices sent in 2026')
  })
})

describe('StatusBadge', () => {
  it('uses the status as label and class', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'overdue' } })
    expect(wrapper.text()).toBe('overdue')
    expect(wrapper.classes()).toContain('overdue')
  })
})
