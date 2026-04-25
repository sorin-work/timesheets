import { createApp } from 'vue'

import App from './App.vue'
import { applyTheme, watchSystemTheme } from './lib/theme'
import { router } from './router'
import './styles.css'

applyTheme()
watchSystemTheme()

createApp(App).use(router).mount('#app')
