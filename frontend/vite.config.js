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
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        // 简化的代码分割策略，避免循环依赖
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            // 将 Vue 相关和 Element Plus 放在一起，避免循环依赖
            if (id.includes('vue') || id.includes('vue-router') || 
                id.includes('element-plus') || id.includes('@element-plus')) {
              return 'vue-vendor'
            }
            // 其他大型库单独分割
            if (id.includes('socket.io')) {
              return 'socketio-vendor'
            }
            // 其他依赖放在一起
            return 'vendor'
          }
        },
      },
    },
  }
}))
