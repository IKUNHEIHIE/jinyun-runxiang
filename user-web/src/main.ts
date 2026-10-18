import { createApp } from 'vue'

import App from './mobile/MobileApp.vue'
import router from './mobile/router'
import './mobile/tokens.css'

const app = createApp(App)

app.use(router)

app.mount('#app')
