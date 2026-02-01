import { reactive, readonly } from 'vue'

import { api, getToken, setToken } from '@/api/client'
import type { TokenResponse, User } from '@/api/types'

const state = reactive<{ user: User | null; ready: boolean }>({ user: null, ready: false })

async function load(): Promise<void> {
  if (state.ready) return
  if (getToken()) {
    try {
      state.user = await api.get<User>('/auth/me')
    } catch {
      setToken(null)
      state.user = null
    }
  }
  state.ready = true
}

function accept(response: TokenResponse): User {
  setToken(response.access_token)
  state.user = response.user
  state.ready = true
  return response.user
}

async function login(email: string, password: string): Promise<User> {
  return accept(await api.post<TokenResponse>('/auth/login', { email, password }))
}

async function signup(name: string, email: string, password: string): Promise<User> {
  return accept(await api.post<TokenResponse>('/auth/signup', { name, email, password }))
}

function logout(): void {
  setToken(null)
  state.user = null
}

function forget(): void {
  state.user = null
}

export function useAuth() {
  return { state: readonly(state), load, login, signup, logout, forget }
}
