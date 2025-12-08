import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { SWRConfig } from 'swr';
import App from './App';
import './index.css'
import './i18n/config'; // Initialize i18n
import { swrConfig, fetcher } from './config/swrConfig';
import * as serviceWorker from './utils/serviceWorker';

// CRITICAL FIX: Prevent redirects to wrong host/port (localhost:3000)
// If page loads on localhost:3000, redirect to same hostname without port (or correct port)
if (typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '3000') {
  const currentPath = window.location.pathname;
  const currentSearch = window.location.search;
  const currentHash = window.location.hash;
  // Redirect to same hostname without port (will use default port 80/443)
  const correctUrl = `${window.location.protocol}//${window.location.hostname}${currentPath}${currentSearch}${currentHash}`;
  console.warn('⚠️ Detected localhost:3000, redirecting to:', correctUrl);
  window.location.replace(correctUrl);
}

// CRITICAL FIX: Ensure root element exists before rendering
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found! Check index.html for <div id="root"></div>');
}

// Add error handler for unhandled errors
window.addEventListener('error', (event) => {
  console.error('🚨 Unhandled error:', event.error);
  // Show error in page if React hasn't rendered
  if (!rootElement.hasChildNodes()) {
    rootElement.innerHTML = `
      <div style="padding: 2rem; font-family: system-ui; max-width: 800px; margin: 0 auto;">
        <h1 style="color: #dc2626;">Application Error</h1>
        <p style="color: #6b7280;">An error occurred while loading the application.</p>
        <pre style="background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; overflow: auto;">
          ${event.error?.message || 'Unknown error'}
          ${event.error?.stack || ''}
        </pre>
        <button onclick="window.location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #2563eb; color: white; border: none; border-radius: 0.25rem; cursor: pointer;">
          Reload Page
        </button>
      </div>
    `;
  }
});

// Debug: Log that we're about to render

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <SWRConfig value={{ ...swrConfig, fetcher }}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <App />
      </BrowserRouter>
    </SWRConfig>
  </React.StrictMode>
);

// Debug: Check if root has content after a short delay
setTimeout(() => {
  if (rootElement.children.length === 0) {
    console.error('⚠️ Root element is empty after render!');
    rootElement.innerHTML = `
      <div style="padding: 2rem; font-family: system-ui; max-width: 800px; margin: 0 auto; background: white; min-height: 100vh;">
        <h1 style="color: #dc2626;">⚠️ Render Issue Detected</h1>
        <p style="color: #6b7280;">React app rendered but root element is empty.</p>
        <p style="color: #6b7280;">Check browser console for errors.</p>
        <button onclick="window.location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #2563eb; color: white; border: none; border-radius: 0.25rem; cursor: pointer;">
          Reload Page
        </button>
      </div>
    `;
  } else {

  }
}, 1000);

// Register service worker for PWA
// Also unregister any old service workers that might be causing redirect issues
if (import.meta.env.PROD) {
  // First, check if we need to unregister old service workers
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((registration) => {
        // Unregister if it's causing issues (user can manually clear cache)
        // We'll keep this commented for now, but can enable if needed
        // registration.unregister();
      });
    });
  }
  
  serviceWorker.register({
    onSuccess: () => {

    },
    onUpdate: () => {

    },
  });
} else {
  // In development, unregister service workers to prevent caching issues
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((registration) => {
        registration.unregister();
      });
    });
  }
}
