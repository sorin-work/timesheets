<script setup lang="ts">
import { computed } from 'vue'

import type { RevenueReport } from '@/api/types'
import { formatMoney } from '@/lib/format'

const props = defineProps<{ report: RevenueReport; currency: string }>()

const MONTHS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
const HEIGHT = 160
const BAR = 14

function valueIn(list: { currency: string; amount: string }[]): number {
  return Number(list.find((a) => a.currency === props.currency)?.amount ?? 0)
}

const bars = computed(() =>
  props.report.months.map((m, i) => ({
    label: MONTHS[i]!,
    month: m.month,
    invoiced: valueIn(m.invoiced),
    paid: valueIn(m.paid),
  })),
)

const max = computed(() => Math.max(1, ...bars.value.flatMap((b) => [b.invoiced, b.paid])))

function h(value: number): number {
  return (value / max.value) * (HEIGHT - 20)
}
</script>

<template>
  <figure class="chart">
    <svg
      :viewBox="`0 0 ${12 * 40} ${HEIGHT + 20}`"
      role="img"
      :aria-label="`Revenue ${report.year}`"
    >
      <g v-for="(bar, i) in bars" :key="bar.month" :transform="`translate(${i * 40 + 5}, 0)`">
        <title>
          {{ bar.month }}: invoiced {{ formatMoney(bar.invoiced, currency) }}, paid
          {{ formatMoney(bar.paid, currency) }}
        </title>
        <rect
          class="invoiced"
          :x="0"
          :y="HEIGHT - h(bar.invoiced)"
          :width="BAR"
          :height="h(bar.invoiced)"
        />
        <rect
          class="paid"
          :x="BAR + 2"
          :y="HEIGHT - h(bar.paid)"
          :width="BAR"
          :height="h(bar.paid)"
        />
        <text :x="BAR" :y="HEIGHT + 15" text-anchor="middle">{{ bar.label }}</text>
      </g>
    </svg>
    <figcaption>
      <span class="key invoiced" /> Invoiced <span class="key paid" /> Paid ({{ currency }})
    </figcaption>
  </figure>
</template>

<style scoped>
.chart {
  margin: 0;
}

svg {
  width: 100%;
  max-height: 14rem;
}

rect.invoiced,
.key.invoiced {
  fill: #a5b4fc;
  background: #a5b4fc;
}

rect.paid,
.key.paid {
  fill: var(--primary);
  background: var(--primary);
}

text {
  font-size: 11px;
  fill: var(--muted);
}

figcaption {
  font-size: 0.8125rem;
  color: var(--muted);
}

.key {
  display: inline-block;
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 2px;
  vertical-align: middle;
  margin-left: 0.5rem;
}
</style>
