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
    // 减少内存占用：禁用某些优化
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        // 更细粒度的代码分割，减少单个文件大小和内存占用
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            if (id.includes('vue') || id.includes('vue-router')) {
              return 'vue-vendor'
            }
            if (id.includes('element-plus')) {
              return 'element-plus'
            }
            if (id.includes('@element-plus/icons-vue')) {
              return 'element-icons'
            }
            // 其他 node_modules 也分割
            return 'vendor'
          }
        },
      },
    },
  }
}))
