import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
    build: {
        outDir: "../static/dist",
        emptyOutDir: true,
        manifest: true,
        // Optimize for better FCP
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