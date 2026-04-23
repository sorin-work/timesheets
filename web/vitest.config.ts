import { fileURLToPath } from 'node:url'

import { configDefaults, defineConfig, mergeConfig } from 'vitest/config'

import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      // Far from UTC on purpose, so date handling bugs show up in tests.
      env: { TZ: 'Pacific/Auckland' },
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
    },
  }),
)
