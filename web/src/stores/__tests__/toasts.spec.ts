import { afterEach, describe, expect, it, vi } from 'vitest'

import { useToasts } from '../toasts'

afterEach(() => vi.useRealTimers())

describe('toasts', () => {
  it('disappear on their own', () => {
    vi.useFakeTimers()
    const { toasts, success } = useToasts()
    success('Saved')
    expect(toasts.map((t) => t.message)).toContain('Saved')
    vi.advanceTimersByTime(4100)
    expect(toasts.map((t) => t.message)).not.toContain('Saved')
  })

  it('can be dismissed', () => {
    const { toasts, error, dismiss } = useToasts()
    const id = error('Boom')
    dismiss(id)
    expect(toasts.find((t) => t.id === id)).toBeUndefined()
  })
})
