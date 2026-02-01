<script setup lang="ts">
import { useAuth } from '@/stores/auth'

const auth = useAuth()
</script>

<template>
  <section>
    <h1>Hello, {{ auth.state.user?.name }}</h1>
  </section>
</template>
