import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import BudgetBar from '../BudgetBar.vue'

describe('BudgetBar', () => {
  it('shows usage against the budget', () => {
    const wrapper = mount(BudgetBar, { props: { usedSeconds: 5 * 3600, budgetHours: '10.00' } })
    expect(wrapper.text()).toContain('5:00 / 10 h')
    expect(wrapper.classes()).toContain('ok')
    expect(wrapper.find('.fill').attributes('style')).toContain('width: 50%')
  })

  it('warns near and over the budget', () => {
    expect(
      mount(BudgetBar, { props: { usedSeconds: 9 * 3600, budgetHours: '10' } }).classes(),
    ).toContain('near')
    const over = mount(BudgetBar, { props: { usedSeconds: 12 * 3600, budgetHours: '10' } })
    expect(over.classes()).toContain('over')
    expect(over.find('.fill').attributes('style')).toContain('width: 100%')
  })
})
