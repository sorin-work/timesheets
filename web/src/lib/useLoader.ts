import { ref, type Ref } from 'vue'

/**
 * Loading and error state around an async fetch. Only the latest call wins, so a
 * slow response for an old filter cannot overwrite a newer one.
 */
export function useLoader<T>(initial: T, fetcher: () => Promise<T>) {
  const data = ref(initial) as Ref<T>
  const loading = ref(true)
  const error = ref('')
  let latest = 0

  async function load(): Promise<void> {
    const call = ++latest
    loading.value = true
    error.value = ''
    try {
      const result = await fetcher()
      if (call === latest) data.value = result
    } catch (e) {
      if (call === latest) error.value = (e as Error).message
    } finally {
      if (call === latest) loading.value = false
    }
  }

  return { data, loading, error, load }
}
