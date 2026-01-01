import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import compression from 'vite-plugin-compression'

export default defineConfig({
    base: '/static/dist/',
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
        compression({ algorithm: 'gzip' }),      // Creates .gz files
        compression({ algorithm: 'brotliCompress', ext: '.br' })  // Creates .br files
    ],
})