import Alpine from 'alpinejs'
import focus from '@alpinejs/focus'
import collapse from '@alpinejs/collapse'

import "@fortawesome/fontawesome-free/css/all.css"

Alpine.plugin(focus)
Alpine.plugin(collapse)

window.Alpine = Alpine

Alpine.start()