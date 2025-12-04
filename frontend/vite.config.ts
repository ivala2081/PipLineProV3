import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Bundle analyzer - disabled in production CI/CD builds
    ...(process.env.ANALYZE === 'true' ? [
      visualizer({
        filename: 'dist/bundle-analysis.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      }),
    ] : []),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0', // Bind to both IPv4 and IPv6
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        timeout: 120000, // 120 second timeout (increased for slow financial performance queries)
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🔴 Proxy error:', err.message);
            console.log('💡 Make sure Flask backend is running on http://127.0.0.1:5000');
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('📤 Proxying:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('📥 Response:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
  build: {
    outDir: 'dist_prod',
    emptyOutDir: true,
    sourcemap: false, // Disable sourcemaps in production for better performance
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // AUTO-REMOVE: All console.log() in production builds (Phase 1 ✅)
        drop_debugger: true, // Remove debugger statements
        pure_funcs: ['console.log', 'console.info', 'console.debug'], // Remove console logs
        passes: 2, // Multiple passes for better optimization
      },
      format: {
        comments: false, // Remove all comments
      },
    },
    rollupOptions: {
      // Tree shaking optimization
      treeshake: {
        moduleSideEffects: false,
        propertyReadSideEffects: false,
        tryCatchDeoptimization: false,
      },
      output: {
        // Ensure vendor-react loads first by making it the first chunk
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: (chunkInfo) => {
          // Force vendor-react to be named first alphabetically
          if (chunkInfo.name === 'vendor-react') {
            return 'js/vendor-react-[hash].js';
          }
          return 'js/[name]-[hash].js';
        },
        manualChunks: (id) => {
          // Node modules chunking
          if (id.includes('node_modules')) {
            // CRITICAL: Bundle ALL React-related packages together FIRST to prevent hook errors
            // This includes react, react-dom, scheduler, and ANY package that uses React
            if (
              id.includes('react') || 
              id.includes('react-dom') || 
              id.includes('scheduler') ||
              id.includes('react-router') ||
              id.includes('react-redux') ||
              id.includes('react-i18next') ||
              id.includes('react-hook-form') ||
              id.includes('react-day-picker') ||
              id.includes('react-hotkeys-hook') ||
              id.includes('react-plotly') ||
              id.includes('react-resizable') ||
              id.includes('@reduxjs') ||
              id.includes('swr') ||
              id.includes('use-sync-external-store') ||
              id.includes('framer-motion') ||
              id.includes('embla-carousel-react') ||
              id.includes('next-themes') ||
              id.includes('vaul') ||
              id.includes('cmdk') ||
              id.includes('input-otp')
            ) {
              return 'vendor-react';
            }
            
            // Radix UI components - these use React, put in vendor-react
            if (id.includes('@radix-ui')) {
              return 'vendor-react'; // Radix UI requires React
            }
            
            // UI component libraries - @headlessui uses React, so put it in vendor-react
            if (id.includes('@headlessui')) {
              return 'vendor-react'; // @headlessui requires React
            }
            if (id.includes('@heroicons') || id.includes('lucide-react')) {
              return 'vendor-ui';
            }
            
            // Chart libraries - split heavy libraries
            if (id.includes('recharts')) {
              return 'vendor-charts-recharts';
            }
            if (id.includes('chart.js') || id.includes('chartjs')) {
              return 'vendor-charts-chartjs';
            }
            if (id.includes('plotly')) {
              return 'vendor-charts-plotly';
            }
            
            // State management (non-React ones)
            if (id.includes('@tanstack/react-query')) {
              return 'vendor-state-query';
            }
            
            // Forms and validation (zod can stay separate, but react-hook-form needs React)
            if (id.includes('zod') && !id.includes('react')) {
              return 'vendor-forms';
            }
            
            // i18n (only core i18next, react-i18next is in vendor-react)
            if (id.includes('i18next') && !id.includes('react-i18next')) {
              return 'vendor-i18n';
            }
            
            // Date utilities
            if (id.includes('date-fns')) {
              return 'vendor-dates';
            }
            
            // Utility libraries
            if (id.includes('clsx') || id.includes('tailwind-merge') || id.includes('class-variance-authority')) {
              return 'vendor-utils';
            }
            
            // Put ALL remaining packages into vendor-react to ensure React loads first
            // This prevents any package from trying to use React before it's loaded
            return 'vendor-react';
          }
          
          // Split large feature modules
          if (id.includes('/pages/')) {
            const pageName = id.split('/pages/')[1].split('.')[0];
            if (['SystemMonitor', 'BusinessAnalytics', 'Reports', 'RevenueAnalytics'].includes(pageName)) {
              return `pages-${pageName.toLowerCase()}`;
            }
            return 'pages';
          }
          
          // Split large component modules
          if (id.includes('/components/trust/')) {
            return 'components-trust';
          }
          if (id.includes('/components/modern/')) {
            return 'components-modern';
          }
          if (id.includes('/components/ui/')) {
            return 'components-ui';
          }
          
          // Split context providers
          if (id.includes('/contexts/')) {
            return 'contexts';
          }
        },
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `images/[name]-[hash][extname]`;
          }
          if (/css/i.test(ext)) {
            return `css/[name]-[hash][extname]`;
          }
          if (/woff|woff2|ttf|eot/i.test(ext)) {
            return `fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
      },
    },
    chunkSizeWarningLimit: 500, // Lower threshold for better splitting
    target: 'esnext', // Target modern browsers for better performance
    cssCodeSplit: true, // Split CSS files for better caching
    reportCompressedSize: false, // Faster builds
    // Additional optimizations
    assetsInlineLimit: 4096, // Inline small assets
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
    exclude: ['@vite/client', '@vite/env'],
  },
})