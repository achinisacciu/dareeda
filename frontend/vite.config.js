import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      'plotly.js/dist/plotly': 'plotly.js-dist-min',
    },
  },
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;

          if (id.includes('plotly.js-dist-min') || id.includes('react-plotly.js')) {
            return 'plotly-vendor';
          }

          if (id.includes('react-router') || id.includes('@remix-run')) {
            return 'router-vendor';
          }

          if (id.includes('axios') || id.includes('zustand')) {
            return 'data-vendor';
          }

          if (id.includes('react') || id.includes('scheduler')) {
            return 'react-vendor';
          }

          return 'vendor';
        },
      },
    },
  },
})
