import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  // plugins 的意思是： 启动 Vite 时加载插件。
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // resolve.alias 的核心作用是，给很长很难写的路径起一个短名字。
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      // 所有 /api 开头的请求都转发到后端，避免跨域问题
    },
  },
})
