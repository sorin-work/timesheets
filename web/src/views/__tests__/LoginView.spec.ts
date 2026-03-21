import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { flush, mockApi, testRouter } from '@/__tests__/helpers'
import { getToken, setToken } from '@/api/client'

import LoginView from '../LoginView.vue'

afterEach(() => {
  vi.unstubAllGlobals()
  setToken(null)
})

async function mountLogin() {
  const router = testRouter([{ path: '/login', component: LoginView }])
  await router.push('/login')
  const wrapper = mount(LoginView, { global: { plugins: [router] } })
  return { wrapper, router }
}

describe('LoginView', () => {
  it('stores the token and goes home after signing in', async () => {
    const fetch = mockApi({
      'POST /api/auth/login': {
        access_token: 'tok-123',
        token_type: 'bearer',
        user: { id: 1, email: 'a@b.c', name: 'A' },
      },
    })
    const { wrapper, router } = await mountLogin()
    await wrapper.find('input[type=email]').setValue('a@b.c')
    await wrapper.find('input[type=password]').setValue('password123')
    await wrapper.find('form').trigger('submit')
    await flush()

    expect(fetch).toHaveBeenCalledOnce()
    expect(JSON.parse(fetch.mock.calls[0]![1]!.body as string)).toEqual({
      email: 'a@b.c',
      password: 'password123',
    })
    expect(getToken()).toBe('tok-123')
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('shows the error message from the api', async () => {
    mockApi({
      'POST /api/auth/login': () => ({
        status: 401,
        body: { error: { code: 'unauthorized', message: 'Invalid email or password' } },
      }),
    })
    const { wrapper } = await mountLogin()
    await wrapper.find('input[type=email]').setValue('a@b.c')
    await wrapper.find('input[type=password]').setValue('nope')
    await wrapper.find('form').trigger('submit')
    await flush()

    expect(wrapper.find('[role=alert]').text()).toBe('Invalid email or password')
    expect(getToken()).toBeNull()
  })
})
