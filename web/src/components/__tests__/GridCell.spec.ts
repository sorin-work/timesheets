import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import GridCell from '../GridCell.vue'

describe('GridCell', () => {
  it('shows the duration as h:mm', () => {
    const wrapper = mount(GridCell, { props: { seconds: 5400, label: 'Mon' } })
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('1:30')
  })

  it('emits minutes when the value changes', async () => {
    const wrapper = mount(GridCell, { props: { seconds: 0, label: 'Mon' } })
    const input = wrapper.find('input')
    await input.setValue('2.5')
    await input.trigger('blur')
    expect(wrapper.emitted('change')).toEqual([[150]])
  })

  it('does not emit when nothing changed', async () => {
    const wrapper = mount(GridCell, { props: { seconds: 3600, label: 'Mon' } })
    const input = wrapper.find('input')
    await input.setValue('1:00')
    await input.trigger('blur')
    expect(wrapper.emitted('change')).toBeUndefined()
  })

  it('marks garbage as invalid', async () => {
    const wrapper = mount(GridCell, { props: { seconds: 0, label: 'Mon' } })
    const input = wrapper.find('input')
    await input.setValue('lots')
    await input.trigger('blur')
    expect(input.classes()).toContain('invalid')
    expect(wrapper.emitted('change')).toBeUndefined()
  })
})
