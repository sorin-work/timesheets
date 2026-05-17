<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, ApiError } from '@/api/client'
import ModalDialog from '@/components/ModalDialog.vue'
import { useAuth } from '@/stores/auth'

const auth = useAuth()
const router = useRouter()

const open = ref(false)
const password = ref('')
const error = ref('')
const busy = ref(false)

async function confirmDelete() {
  busy.value = true
  error.value = ''
  try {
    await api.delete('/auth/me', { password: password.value })
    auth.logout()
    await router.push({ name: 'signup' })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'Could not delete the account'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="card danger-zone">
    <h2>Delete account</h2>
    <p class="muted">
      Permanently deletes your clients, projects, time entries and invoices. Export anything you
      want to keep first.
    </p>
    <button type="button" class="danger" @click="open = true">Delete my account</button>

    <ModalDialog v-if="open" title="Delete your account?" @close="open = false">
      <form class="form" @submit.prevent="confirmDelete">
        <p>This cannot be undone. Enter your password to confirm.</p>
        <label>
          Password
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="actions">
          <button type="button" @click="open = false">Cancel</button>
          <button type="submit" class="danger" :disabled="busy">Delete everything</button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>

<style scoped>
.danger-zone {
  border-color: color-mix(in srgb, var(--danger) 40%, var(--border));
}

h2 {
  font-size: 1rem;
  margin: 0 0 0.25rem;
}
</style>
