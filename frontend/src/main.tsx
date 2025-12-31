import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { SWRConfig } from 'swr';
import App from './App';
import './index.css'
import './i18n/config'; // Initialize i18n
import { swrConfig, fetcher } from './config/swrConfig';
import * as serviceWorker from './utils/serviceWorker';

// Log version for debugging
console.log('PipLinePro Frontend - Version 2.0 - Enhanced Error Handling');

// CRITICAL FIX: Prevent redirects to wrong host/port (localhost:3000)
// If page loads on localhost:3000, redirect to same hostname without port (or correct port)
if (typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '3000') {
  // #region agent log (dev only)
  if (import.meta.env.DEV) {
    fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'main.tsx:redirect-check',message:'Detected localhost:3000 (pre-redirect)',data:{href:window.location.href,hostname:window.location.hostname,port:window.location.port,pathname:window.location.pathname},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
  }
  // #endregion
  const currentPath = window.location.pathname;
  const currentSearch = window.location.search;
  const currentHash = window.location.hash;
  // Redirect to same hostname without port (will use default port 80/443)
  const correctUrl = `${window.location.protocol}//${window.location.hostname}${currentPath}${currentSearch}${currentHash}`;
  console.warn('⚠️ Detected localhost:3000, redirecting to:', correctUrl);
  // #region agent log (dev only)
  if (import.meta.env.DEV) {
    fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'main.tsx:redirect',message:'Redirecting away from localhost:3000',data:{from:window.location.href,to:correctUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
  }
  // #endregion
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
  // #region agent log (dev only)
  if (import.meta.env.DEV) {
    fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'main.tsx:window-error',message:'window.error event',data:{message:event.error?.message||String(event.message||''),filename:(event as any)?.filename,lineno:(event as any)?.lineno,colno:(event as any)?.colno,href:window.location.href},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
  }
  // #endregion
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

window.addEventListener('unhandledrejection', (event) => {
  // #region agent log (dev only)
  if (import.meta.env.DEV) {
    fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'main.tsx:unhandledrejection',message:'window.unhandledrejection event',data:{reasonMessage:(event.reason as any)?.message||String(event.reason||''),href:window.location.href},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
  }
  // #endregion
  
  // Handle chunk loading errors specifically
  const reason = event.reason;
  const isChunkError = 
    (reason?.message?.includes && reason.message.includes('Failed to fetch')) ||
    (reason?.message?.includes && reason.message.includes('Loading chunk')) ||
    (reason?.message?.includes && reason.message.includes('ChunkLoadError')) ||
    reason?.name === 'ChunkLoadError' ||
    (reason?.message?.includes && reason.message.includes('Failed to fetch dynamically imported module'));
  
  if (isChunkError) {
    console.error('🚨 Chunk loading error detected:', reason);
    console.warn('This usually means the browser is trying to load an outdated chunk file.');
    console.warn('Try refreshing the page (Ctrl+F5 for hard refresh) or clearing browser cache.');
    
    // Don't prevent default - let the error boundary handle it
    // But log it for debugging
    if (import.meta.env.PROD) {
      // In production, we might want to show a user-friendly message
      // But for now, let the error boundary handle it
    }
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
  serviceWorker.register({
    onSuccess: (registration) => {
      console.log('[SW] Service worker registered successfully');
      // Check for updates every 5 minutes
      setInterval(() => {
        registration?.update();
      }, 5 * 60 * 1000);
    },
    onUpdate: (registration) => {
      console.log('[SW] New service worker available! Updating...');
      // Force the new service worker to activate immediately
      if (registration && registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        // Reload the page to get the new version
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    },
  });
} else {
  // In development, unregister service workers to prevent caching issues
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((registration) => {
        console.log('[SW] Unregistering service worker in development');
        registration.unregister();
      });
    });
  }
}
