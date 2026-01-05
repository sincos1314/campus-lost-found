import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    mode === 'development' ? vueDevTools() : undefined,
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: true,
    port: 5173
  },
  build: {
    sourcemap: false,
    chunkSizeWarningLimit: 2000,
    // 使用 esbuild 压缩（更快，不需要额外依赖）
    minify: 'esbuild',
    rollupOptions: {
      output: {
        // 代码分割，减少单个文件大小和内存占用
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router'],
          'element-plus': ['element-plus'],
          'element-icons': ['@element-plus/icons-vue'],
        },
      },
    },
  }
}))
