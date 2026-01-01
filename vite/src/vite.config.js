import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
    build: {
        outDir: "../static/dist",
        emptyOutDir: true,
        manifest: true,
        minify: 'terser',
        cssMinify: true,
        cssCodeSplit: true,
        terserOptions: {
            compress: {
                drop_console: true, // Remove console.logs in production
                passes: 2
            }
        }
    },
    plugins: [
        tailwindcss(),
    ],
})