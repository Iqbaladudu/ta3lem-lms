import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
    build: {
        outDir: "../static/dist",
        emptyOutDir: true,
        manifest: true,
        rollupOptions: {
            input: {
                main: './src/index.js'
            }
        }
    },
    plugins: [
        tailwindcss(),
    ],
})