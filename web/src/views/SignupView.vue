<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { useAuth } from '@/stores/auth'

const auth = useAuth()
const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const fieldErrors = ref<Record<string, string>>({})
const busy = ref(false)

async function submit() {
  error.value = ''
  fieldErrors.value = {}
  busy.value = true
  try {
    await auth.signup(name.value, email.value, password.value)
    await router.push('/')
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.message
      fieldErrors.value = e.fieldErrors()
    } else {
      error.value = 'Something went wrong'
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <form class="card auth-card" @submit.prevent="submit">
      <h1>Create your account</h1>
      <label>
        Your name
        <input v-model="name" autocomplete="name" required />
        <small v-if="fieldErrors.name" class="error">{{ fieldErrors.name }}</small>
      </label>
      <label>
        Email
        <input v-model="email" type="email" autocomplete="email" required />
        <small v-if="fieldErrors.email" class="error">{{ fieldErrors.email }}</small>
      </label>
      <label>
        Password
        <input
          v-model="password"
          type="password"
          autocomplete="new-password"
          minlength="8"
          required
        />
        <small class="muted">At least 8 characters.</small>
      </label>
      <p v-if="error && !Object.keys(fieldErrors).length" class="error" role="alert">
        {{ error }}
      </p>
      <button class="primary" type="submit" :disabled="busy">
        {{ busy ? 'Creating…' : 'Create account' }}
      </button>
      <p class="muted">Already registered? <RouterLink to="/login">Sign in</RouterLink></p>
    </form>
  </div>
</template>
