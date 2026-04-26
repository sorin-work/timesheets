<script setup lang="ts">
export interface TaxLine {
  name: string
  rate: string
}

const taxes = defineModel<TaxLine[]>({ required: true })

function add() {
  taxes.value = [...taxes.value, { name: 'VAT', rate: '19' }]
}

function remove(index: number) {
  taxes.value = taxes.value.filter((_, i) => i !== index)
}
</script>

<template>
  <fieldset class="taxes">
    <legend>Taxes</legend>
    <p v-if="!taxes.length" class="muted none">No taxes.</p>
    <div v-for="(tax, i) in taxes" :key="i" class="tax-row">
      <input v-model="tax.name" aria-label="Tax name" maxlength="60" required />
      <input v-model="tax.rate" aria-label="Rate %" inputmode="decimal" required />
      <span>%</span>
      <button type="button" @click="remove(i)">Remove</button>
    </div>
    <button type="button" :disabled="taxes.length >= 5" @click="add">Add tax</button>
  </fieldset>
</template>

<style scoped>
.taxes {
  border: 1px solid var(--border);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
}

.none {
  margin: 0;
}

.tax-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.tax-row input:last-of-type {
  width: 5rem;
}
</style>
