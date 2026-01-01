import Alpine from 'alpinejs'
import focus from '@alpinejs/focus'
import collapse from '@alpinejs/collapse'
import htmx from 'htmx.org'

import "@fortawesome/fontawesome-free/css/all.css"

// Initialize Alpine.js plugins
Alpine.plugin(focus)
Alpine.plugin(collapse)

// Expose libraries globally for Django templates
window.Alpine = Alpine
window.htmx = htmx

Alpine.start()