import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import PaginationBar from '../PaginationBar.vue'

describe('PaginationBar', () => {
  it('disables previous on the first page', async () => {
    const wrapper = mount(PaginationBar, { props: { page: 1, pages: 3, total: 70 } })
    const [prev, next] = wrapper.findAll('button')
    expect(prev!.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Page 1 of 3')
    await next!.trigger('click')
    expect(wrapper.emitted('change')).toEqual([[2]])
  })

  it('disables next on the last page', () => {
    const wrapper = mount(PaginationBar, { props: { page: 3, pages: 3, total: 70 } })
    expect(wrapper.findAll('button')[1]!.attributes('disabled')).toBeDefined()
  })
})
