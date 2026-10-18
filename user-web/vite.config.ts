import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { androidPublicAssets } from './scripts/android-public-assets.mjs'

export default defineConfig(({mode}) => ({
  plugins: [vue(), ...(mode === 'android' ? [androidPublicAssets()] : [])],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 5174,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    target: 'es2017',
    copyPublicDir: mode !== 'android',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: id => id.includes('node_modules') && /[\\/](@vue|vue|vue-router)[\\/]/.test(id) ? 'vue-vendor' : undefined
      }
    }
  }
}))
