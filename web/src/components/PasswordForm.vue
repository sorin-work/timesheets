<script setup lang="ts">
import { reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'

const form = reactive({ current_password: '', new_password: '', confirm: '' })
const errors = ref<Record<string, string>>({})
const done = ref(false)
const busy = ref(false)

async function submit() {
  errors.value = {}
  done.value = false
  if (form.new_password !== form.confirm) {
    errors.value = { confirm: 'Passwords do not match' }
    return
  }
  busy.value = true
  try {
    await api.post('/auth/password', {
      current_password: form.current_password,
      new_password: form.new_password,
    })
    Object.assign(form, { current_password: '', new_password: '', confirm: '' })
    done.value = true
  } catch (e) {
    if (e instanceof ApiError) errors.value = { ...e.fieldErrors(), form: e.message }
    else throw e
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="card form" @submit.prevent="submit">
    <h2>Change password</h2>
    <label>
      Current password
      <input
        v-model="form.current_password"
        type="password"
        autocomplete="current-password"
        required
      />
      <small v-if="errors.current_password" class="error">{{ errors.current_password }}</small>
    </label>
    <div class="row">
      <label>
        New password
        <input
          v-model="form.new_password"
          type="password"
          autocomplete="new-password"
          minlength="8"
          required
        />
        <small v-if="errors.new_password" class="error">{{ errors.new_password }}</small>
      </label>
      <label>
        Repeat new password
        <input v-model="form.confirm" type="password" autocomplete="new-password" required />
        <small v-if="errors.confirm" class="error">{{ errors.confirm }}</small>
      </label>
    </div>
    <div class="actions">
      <span v-if="done" class="saved">Password changed</span>
      <button type="submit" :disabled="busy">Change password</button>
    </div>
  </form>
</template>

<style scoped>
h2 {
  font-size: 1rem;
  margin: 0;
}

.saved {
  color: var(--success);
  align-self: center;
}
</style>
