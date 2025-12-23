/**
 * UI/UX Debug Instrumentation
 * Captures runtime UI/UX data for analysis
 */

// Use same-origin endpoint to avoid mixed-content/CORS issues in production HTTPS deployments
const SERVER_ENDPOINT = '/api/v1/monitoring/client-log';

export const logUIUXData = (location: string, message: string, data: any, hypothesisId: string) => {
  if (!import.meta.env.DEV) return;
  fetch(SERVER_ENDPOINT, {
    method: 'POST',
    mode: 'no-cors',
    keepalive: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      location,
      message,
      data,
      timestamp: Date.now(),
      sessionId: 'debug-session',
      runId: 'run1',
      hypothesisId
    })
  }).catch(() => {});
};

export const analyzeColorUsage = () => {
  const elements = document.querySelectorAll('*');
  const colorStats: Record<string, number> = {};
  let blueCount = 0;
  let gradientCount = 0;
  
  elements.forEach(el => {
    const computed = getComputedStyle(el);
    const bgColor = computed.backgroundColor;
    const color = computed.color;
    const bgImage = computed.backgroundImage;
    
    if (bgColor && (bgColor.includes('rgb(59, 130, 246)') || bgColor.includes('#3b82f6') || bgColor.includes('blue'))) {
      blueCount++;
    }
    if (bgImage && bgImage !== 'none' && bgImage.includes('gradient')) {
      gradientCount++;
    }
    
    const key = `${bgColor}-${color}`;
    colorStats[key] = (colorStats[key] || 0) + 1;
  });
  
  logUIUXData(
    'uiDebugInstrumentation.ts:analyzeColorUsage',
    'Color usage analysis',
    { blueCount, gradientCount, uniqueColorCombos: Object.keys(colorStats).length },
    'A,E'
  );
};

export const checkResponsiveLayout = () => {
  const width = window.innerWidth;
  const breakpoint = width < 640 ? 'sm' : width < 768 ? 'md' : width < 1024 ? 'lg' : width < 1280 ? 'xl' : '2xl';
  
  const sidebar = document.querySelector('[class*="sidebar"], .lg\\:fixed');
  const header = document.querySelector('header');
  const main = document.querySelector('main');
  
  logUIUXData(
    'uiDebugInstrumentation.ts:checkResponsiveLayout',
    'Responsive layout check',
    {
      width,
      breakpoint,
      sidebarVisible: sidebar ? getComputedStyle(sidebar as HTMLElement).display !== 'none' : false,
      headerHeight: header ? getComputedStyle(header).height : null,
      mainPadding: main ? getComputedStyle(main).padding : null
    },
    'D'
  );
};

export const checkDesignSystemConflicts = () => {
  const root = document.documentElement;
  const cssVars = {
    primary500: getComputedStyle(root).getPropertyValue('--color-primary-500'),
    businessPrimary: getComputedStyle(root).getPropertyValue('--business-primary'),
    primary: getComputedStyle(root).getPropertyValue('--primary'),
  };
  
  logUIUXData(
    'uiDebugInstrumentation.ts:checkDesignSystemConflicts',
    'Design system variables check',
    cssVars,
    'B'
  );
};

export const initializeUIUXDebugging = () => {
  if (!import.meta.env.DEV) return;
  // Run after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        analyzeColorUsage();
        checkResponsiveLayout();
        checkDesignSystemConflicts();
      }, 1000);
    });
  } else {
    setTimeout(() => {
      analyzeColorUsage();
      checkResponsiveLayout();
      checkDesignSystemConflicts();
    }, 1000);
  }
  
  // Check on resize
  window.addEventListener('resize', () => {
    checkResponsiveLayout();
  });
};

