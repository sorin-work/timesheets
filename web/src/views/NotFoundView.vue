<template>
  <section class="not-found">
    <h1>Page not found</h1>
    <p class="muted">The page you were looking for does not exist or was moved.</p>
    <RouterLink class="button primary" to="/">Back to the dashboard</RouterLink>
  </section>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: 4rem 1rem;
}
</style>
