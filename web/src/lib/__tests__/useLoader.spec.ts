import { describe, expect, it } from 'vitest'

import { useLoader } from '../useLoader'

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((r) => (resolve = r))
  return { promise, resolve }
}

describe('useLoader', () => {
  it('tracks loading and errors', async () => {
    const loader = useLoader<number[]>([], () => Promise.reject(new Error('down')))
    await loader.load()
    expect(loader.loading.value).toBe(false)
    expect(loader.error.value).toBe('down')
  })

  it('ignores responses that arrive after a newer request', async () => {
    const calls = [deferred<string>(), deferred<string>()]
    let i = 0
    const loader = useLoader('', () => calls[i++]!.promise)
    const first = loader.load()
    const second = loader.load()
    calls[1]!.resolve('new')
    await second
    calls[0]!.resolve('old')
    await first
    expect(loader.data.value).toBe('new')
  })
})
