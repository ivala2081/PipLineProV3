/**
 * Responsive Automation System
 * Automatically handles responsive design for all UI elements
 * Including typography scaling, component resizing, and viewport adjustments
 */

class ResponsiveAutomation {
  constructor() {
    this.breakpoints = {
      xs: 480,
      sm: 576,
      md: 768,
      lg: 992,
      xl: 1200,
      '2xl': 1400
    };
    
    this.currentBreakpoint = this.getCurrentBreakpoint();
    this.resizeObserver = null;
    this.intersectionObserver = null;
    
    this.init();
  }
  
  init() {
    this.setupResizeObserver();
    this.setupIntersectionObserver();
    this.setupViewportScaling();
    this.setupTypographyScaling();
    this.setupComponentScaling();
    this.setupTouchOptimizations();
    this.setupPerformanceOptimizations();
    
    // Initial setup
    this.updateResponsiveClasses();
    this.updateFluidScaling();
    
    // Listen for window resize
    window.addEventListener('resize', this.debounce(() => {
      this.handleResize();
    }, 100));
    
    // Listen for orientation change
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.handleResize();
      }, 100);
    });
    
    // Listen for DOM changes
    this.observeDOMChanges();
  }
  
  /**
   * Get current breakpoint based on window width
   */
  getCurrentBreakpoint() {
    const width = window.innerWidth;
    
    if (width >= this.breakpoints['2xl']) return '2xl';
    if (width >= this.breakpoints.xl) return 'xl';
    if (width >= this.breakpoints.lg) return 'lg';
    if (width >= this.breakpoints.md) return 'md';
    if (width >= this.breakpoints.sm) return 'sm';
    return 'xs';
  }
  
  /**
   * Handle window resize events
   */
  handleResize() {
    const newBreakpoint = this.getCurrentBreakpoint();
    
    if (newBreakpoint !== this.currentBreakpoint) {
      this.currentBreakpoint = newBreakpoint;
      this.updateResponsiveClasses();
      this.updateFluidScaling();
      this.updateComponentLayouts();
      
      // Dispatch custom event for other scripts
      window.dispatchEvent(new CustomEvent('breakpointChange', {
        detail: { breakpoint: newBreakpoint }
      }));
    }
    
    // Always update fluid scaling on resize
    this.updateFluidScaling();
  }
  
  /**
   * Update responsive utility classes based on current breakpoint
   */
  updateResponsiveClasses() {
    const body = document.body;
    
    // Remove all breakpoint classes
    Object.keys(this.breakpoints).forEach(breakpoint => {
      body.classList.remove(`breakpoint-${breakpoint}`);
    });
    
    // Add current breakpoint class
    body.classList.add(`breakpoint-${this.currentBreakpoint}`);
    
    // Update responsive visibility classes
    this.updateVisibilityClasses();
  }
  
  /**
   * Update visibility classes based on breakpoint
   */
  updateVisibilityClasses() {
    const elements = document.querySelectorAll('[class*="d-"]');
    
    elements.forEach(element => {
      const classes = element.className.split(' ');
      
      classes.forEach(className => {
        if (className.startsWith('d-')) {
          const [display, breakpoint] = className.split('-');
          
          if (breakpoint && this.breakpoints[breakpoint]) {
            const shouldShow = this.shouldShowAtBreakpoint(breakpoint);
            element.style.display = shouldShow ? '' : 'none';
          }
        }
      });
    });
  }
  
  /**
   * Check if element should be visible at current breakpoint
   */
  shouldShowAtBreakpoint(breakpoint) {
    const currentIndex = Object.keys(this.breakpoints).indexOf(this.currentBreakpoint);
    const breakpointIndex = Object.keys(this.breakpoints).indexOf(breakpoint);
    
    return currentIndex >= breakpointIndex;
  }
  
  /**
   * Update fluid scaling for typography and spacing
   */
  updateFluidScaling() {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Calculate fluid scaling factors
    const widthFactor = Math.min(viewportWidth / 1200, 1.5);
    const heightFactor = Math.min(viewportHeight / 800, 1.3);
    const scaleFactor = Math.min(widthFactor, heightFactor);
    
    // Update CSS custom properties for fluid scaling
    document.documentElement.style.setProperty('--fluid-scale-factor', scaleFactor);
    document.documentElement.style.setProperty('--viewport-width', `${viewportWidth}px`);
    document.documentElement.style.setProperty('--viewport-height', `${viewportHeight}px`);
    
    // Update typography scaling
    this.updateTypographyScaling(scaleFactor);
    
    // Update spacing scaling
    this.updateSpacingScaling(scaleFactor);
  }
  
  /**
   * Update typography scaling based on viewport
   */
  updateTypographyScaling(scaleFactor) {
    const baseFontSize = 16; // Base font size in pixels
    const scaledFontSize = baseFontSize * scaleFactor;
    
    document.documentElement.style.fontSize = `${scaledFontSize}px`;
    
    // Update fluid text sizes
    const fluidTextSizes = {
      '--fluid-text-xs': Math.max(12, 12 * scaleFactor),
      '--fluid-text-sm': Math.max(14, 14 * scaleFactor),
      '--fluid-text-base': Math.max(16, 16 * scaleFactor),
      '--fluid-text-lg': Math.max(18, 18 * scaleFactor),
      '--fluid-text-xl': Math.max(20, 20 * scaleFactor),
      '--fluid-text-2xl': Math.max(24, 24 * scaleFactor),
      '--fluid-text-3xl': Math.max(30, 30 * scaleFactor),
      '--fluid-text-4xl': Math.max(36, 36 * scaleFactor),
      '--fluid-text-5xl': Math.max(48, 48 * scaleFactor)
    };
    
    Object.entries(fluidTextSizes).forEach(([property, value]) => {
      document.documentElement.style.setProperty(property, `${value}px`);
    });
  }
  
  /**
   * Update spacing scaling based on viewport
   */
  updateSpacingScaling(scaleFactor) {
    const fluidSpacing = {
      '--fluid-space-xs': Math.max(4, 4 * scaleFactor),
      '--fluid-space-sm': Math.max(8, 8 * scaleFactor),
      '--fluid-space-md': Math.max(16, 16 * scaleFactor),
      '--fluid-space-lg': Math.max(24, 24 * scaleFactor),
      '--fluid-space-xl': Math.max(32, 32 * scaleFactor),
      '--fluid-space-2xl': Math.max(48, 48 * scaleFactor)
    };
    
    Object.entries(fluidSpacing).forEach(([property, value]) => {
      document.documentElement.style.setProperty(property, `${value}px`);
    });
  }
  
  /**
   * Setup viewport-based scaling
   */
  setupViewportScaling() {
    // Add viewport meta tag if not present
    if (!document.querySelector('meta[name="viewport"]')) {
      const viewport = document.createElement('meta');
      viewport.name = 'viewport';
      viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
      document.head.appendChild(viewport);
    }
    
    // Update viewport scaling on load
    this.updateViewportScaling();
  }
  
  /**
   * Update viewport scaling
   */
  updateViewportScaling() {
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      const scale = Math.min(window.innerWidth / 1200, 1.5);
      viewport.content = `width=device-width, initial-scale=${scale}, maximum-scale=5.0, user-scalable=yes`;
    }
  }
  
  /**
   * Setup typography scaling
   */
  setupTypographyScaling() {
    // Apply fluid typography to all text elements
    const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, a, button, input, textarea, label');
    
    textElements.forEach(element => {
      this.applyFluidTypography(element);
    });
  }
  
  /**
   * Apply fluid typography to an element
   */
  applyFluidTypography(element) {
    const computedStyle = window.getComputedStyle(element);
    const fontSize = parseFloat(computedStyle.fontSize);
    
    if (fontSize) {
      // Calculate fluid font size based on viewport
      const viewportWidth = window.innerWidth;
      const fluidSize = Math.max(fontSize * 0.8, fontSize * (viewportWidth / 1200));
      
      element.style.fontSize = `${fluidSize}px`;
    }
  }
  
  /**
   * Setup component scaling
   */
  setupComponentScaling() {
    // Scale components based on viewport
    this.scaleComponents();
    
    // Listen for new components being added
    this.observeComponentChanges();
  }
  
  /**
   * Scale components based on viewport
   */
  scaleComponents() {
    const components = {
      '.btn, .login-btn': { minHeight: 44, padding: 12 },
      '.form-input, .form-control': { minHeight: 44, padding: 12 },
      '.card, .glass-card': { padding: 16 },
      '.modal-dialog': { margin: 16 },
      '.navbar': { padding: 12 },
      '.sidebar': { width: 240 }
    };
    
    const viewportWidth = window.innerWidth;
    const scaleFactor = Math.min(viewportWidth / 1200, 1.5);
    
    Object.entries(components).forEach(([selector, properties]) => {
      const elements = document.querySelectorAll(selector);
      
      elements.forEach(element => {
        Object.entries(properties).forEach(([property, value]) => {
          const scaledValue = value * scaleFactor;
          
          if (property === 'minHeight' || property === 'minWidth') {
            element.style[property] = `${Math.max(scaledValue, 44)}px`;
          } else if (property === 'padding') {
            element.style.padding = `${scaledValue}px`;
          } else if (property === 'margin') {
            element.style.margin = `${scaledValue}px`;
          } else if (property === 'width') {
            element.style.width = `${scaledValue}px`;
          }
        });
      });
    });
  }
  
  /**
   * Setup touch optimizations for mobile
   */
  setupTouchOptimizations() {
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
      document.body.classList.add('touch-device');
      
      // Increase touch targets on mobile
      this.optimizeTouchTargets();
      
      // Add touch event listeners
      this.setupTouchEvents();
    }
  }
  
  /**
   * Optimize touch targets for mobile devices
   */
  optimizeTouchTargets() {
    const touchTargets = document.querySelectorAll('.btn, .nav-link, .form-check-input, .dropdown-toggle');
    
    touchTargets.forEach(target => {
      const rect = target.getBoundingClientRect();
      
      if (rect.height < 44 || rect.width < 44) {
        target.style.minHeight = '44px';
        target.style.minWidth = '44px';
        target.style.padding = '12px 16px';
      }
    });
  }
  
  /**
   * Setup touch event listeners
   */
  setupTouchEvents() {
    // Prevent zoom on double tap
    let lastTouchEnd = 0;
    document.addEventListener('touchend', (event) => {
      const now = (new Date()).getTime();
      if (now - lastTouchEnd <= 300) {
        event.preventDefault();
      }
      lastTouchEnd = now;
    }, false);
    
    // Add touch feedback
    document.addEventListener('touchstart', (event) => {
      const target = event.target.closest('.btn, .nav-link, .card');
      if (target) {
        target.style.transform = 'scale(0.98)';
        target.style.transition = 'transform 0.1s ease';
      }
    });
    
    document.addEventListener('touchend', (event) => {
      const target = event.target.closest('.btn, .nav-link, .card');
      if (target) {
        target.style.transform = 'scale(1)';
      }
    });
  }
  
  /**
   * Setup performance optimizations
   */
  setupPerformanceOptimizations() {
    // Use requestAnimationFrame for smooth animations
    this.useRequestAnimationFrame();
    
    // Optimize scroll performance
    this.optimizeScrollPerformance();
    
    // Lazy load images and components
    this.setupLazyLoading();
  }
  
  /**
   * Use requestAnimationFrame for smooth animations
   */
  useRequestAnimationFrame() {
    // Override scroll and resize handlers to use requestAnimationFrame
    const originalScrollHandler = window.onscroll;
    const originalResizeHandler = window.onresize;
    
    if (originalScrollHandler) {
      window.onscroll = () => {
        requestAnimationFrame(originalScrollHandler);
      };
    }
    
    if (originalResizeHandler) {
      window.onresize = () => {
        requestAnimationFrame(originalResizeHandler);
      };
    }
  }
  
  /**
   * Optimize scroll performance
   */
  optimizeScrollPerformance() {
    // Add will-change to elements that will animate
    const animatedElements = document.querySelectorAll('.sidebar, .modal, .navbar-collapse');
    
    animatedElements.forEach(element => {
      element.style.willChange = 'transform';
      element.style.backfaceVisibility = 'hidden';
    });
  }
  
  /**
   * Setup lazy loading for images and components
   */
  setupLazyLoading() {
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            imageObserver.unobserve(img);
          }
        });
      });
      
      images.forEach(img => imageObserver.observe(img));
    }
  }
  
  /**
   * Setup resize observer for dynamic content
   */
  setupResizeObserver() {
    if ('ResizeObserver' in window) {
      this.resizeObserver = new ResizeObserver(entries => {
        entries.forEach(entry => {
          this.handleElementResize(entry.target, entry.contentRect);
        });
      });
    }
  }
  
  /**
   * Handle element resize
   */
  handleElementResize(element, rect) {
    // Update component scaling for resized elements
    this.scaleComponent(element, rect);
    
    // Update layout if needed
    this.updateLayout(element);
  }
  
  /**
   * Scale a specific component
   */
  scaleComponent(element, rect) {
    const scaleFactor = Math.min(rect.width / 1200, 1.5);
    
    // Apply scaling based on element type
    if (element.classList.contains('btn') || element.classList.contains('login-btn')) {
      element.style.minHeight = `${Math.max(44, 44 * scaleFactor)}px`;
      element.style.padding = `${12 * scaleFactor}px ${16 * scaleFactor}px`;
    } else if (element.classList.contains('form-input') || element.classList.contains('form-control')) {
      element.style.minHeight = `${Math.max(44, 44 * scaleFactor)}px`;
      element.style.padding = `${12 * scaleFactor}px ${16 * scaleFactor}px`;
    } else if (element.classList.contains('card') || element.classList.contains('glass-card')) {
      element.style.padding = `${16 * scaleFactor}px`;
    }
  }
  
  /**
   * Update layout for resized elements
   */
  updateLayout(element) {
    // Trigger layout recalculation
    element.style.transform = 'translateZ(0)';
    
    // Update grid layouts if needed
    if (element.classList.contains('row') || element.classList.contains('col')) {
      this.updateGridLayout();
    }
  }
  
  /**
   * Update grid layout
   */
  updateGridLayout() {
    const grids = document.querySelectorAll('.row, .metrics-grid');
    
    grids.forEach(grid => {
      // Force grid recalculation
      grid.style.display = 'none';
      grid.offsetHeight; // Force reflow
      grid.style.display = '';
    });
  }
  
  /**
   * Setup intersection observer for visibility-based optimizations
   */
  setupIntersectionObserver() {
    if ('IntersectionObserver' in window) {
      this.intersectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.handleElementVisible(entry.target);
          } else {
            this.handleElementHidden(entry.target);
          }
        });
      }, {
        threshold: 0.1,
        rootMargin: '50px'
      });
    }
  }
  
  /**
   * Handle element becoming visible
   */
  handleElementVisible(element) {
    // Apply animations and optimizations for visible elements
    element.classList.add('visible');
    
    // Scale component if needed
    this.scaleComponent(element, element.getBoundingClientRect());
  }
  
  /**
   * Handle element becoming hidden
   */
  handleElementHidden(element) {
    // Remove optimizations for hidden elements
    element.classList.remove('visible');
  }
  
  /**
   * Observe DOM changes for new elements
   */
  observeDOMChanges() {
    if ('MutationObserver' in window) {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              this.handleNewElement(node);
            }
          });
        });
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }
  
  /**
   * Handle new elements being added to DOM
   */
  handleNewElement(element) {
    // Apply responsive classes
    this.applyResponsiveClasses(element);
    
    // Apply fluid typography
    this.applyFluidTypography(element);
    
    // Scale component if needed
    this.scaleComponent(element, element.getBoundingClientRect());
    
    // Observe for resize if needed
    if (this.resizeObserver) {
      this.resizeObserver.observe(element);
    }
    
    // Observe for intersection if needed
    if (this.intersectionObserver) {
      this.intersectionObserver.observe(element);
    }
  }
  
  /**
   * Apply responsive classes to element
   */
  applyResponsiveClasses(element) {
    const breakpoint = this.currentBreakpoint;
    
    // Add breakpoint-specific classes
    element.classList.add(`breakpoint-${breakpoint}`);
    
    // Add responsive utility classes based on element type
    if (element.classList.contains('btn')) {
      element.classList.add('btn-responsive');
    }
    
    if (element.classList.contains('card')) {
      element.classList.add('card-responsive');
    }
    
    if (element.classList.contains('form-input')) {
      element.classList.add('input-responsive');
    }
  }
  
  /**
   * Observe component changes
   */
  observeComponentChanges() {
    // Observe for dynamic component changes
    const componentSelectors = '.btn, .card, .form-input, .modal, .sidebar';
    
    document.addEventListener('DOMContentLoaded', () => {
      const components = document.querySelectorAll(componentSelectors);
      
      components.forEach(component => {
        if (this.resizeObserver) {
          this.resizeObserver.observe(component);
        }
      });
    });
  }
  
  /**
   * Update component layouts
   */
  updateComponentLayouts() {
    // Update specific component layouts based on breakpoint
    this.updateSidebarLayout();
    this.updateModalLayout();
    this.updateFormLayout();
    this.updateNavigationLayout();
  }
  
  /**
   * Update sidebar layout
   */
  updateSidebarLayout() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    const breakpoint = this.currentBreakpoint;
    
    if (breakpoint === 'xs' || breakpoint === 'sm') {
      sidebar.style.transform = 'translateX(-100%)';
      sidebar.classList.add('mobile-sidebar');
    } else {
      sidebar.style.transform = 'translateX(0)';
      sidebar.classList.remove('mobile-sidebar');
    }
  }
  
  /**
   * Update modal layout
   */
  updateModalLayout() {
    const modals = document.querySelectorAll('.modal-dialog');
    
    modals.forEach(modal => {
      const breakpoint = this.currentBreakpoint;
      
      if (breakpoint === 'xs' || breakpoint === 'sm') {
        modal.style.margin = '16px';
        modal.style.maxWidth = 'calc(100% - 32px)';
      } else {
        modal.style.margin = '';
        modal.style.maxWidth = '';
      }
    });
  }
  
  /**
   * Update form layout
   */
  updateFormLayout() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
      const breakpoint = this.currentBreakpoint;
      
      if (breakpoint === 'xs' || breakpoint === 'sm') {
        form.classList.add('mobile-form');
      } else {
        form.classList.remove('mobile-form');
      }
    });
  }
  
  /**
   * Update navigation layout
   */
  updateNavigationLayout() {
    const navs = document.querySelectorAll('.navbar-nav');
    
    navs.forEach(nav => {
      const breakpoint = this.currentBreakpoint;
      
      if (breakpoint === 'xs' || breakpoint === 'sm') {
        nav.classList.add('mobile-nav');
      } else {
        nav.classList.remove('mobile-nav');
      }
    });
  }
  
  /**
   * Debounce function for performance
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  /**
   * Get current responsive state
   */
  getResponsiveState() {
    return {
      breakpoint: this.currentBreakpoint,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      isMobile: this.currentBreakpoint === 'xs' || this.currentBreakpoint === 'sm',
      isTablet: this.currentBreakpoint === 'md',
      isDesktop: this.currentBreakpoint === 'lg' || this.currentBreakpoint === 'xl' || this.currentBreakpoint === '2xl',
      isTouchDevice: 'ontouchstart' in window || navigator.maxTouchPoints > 0
    };
  }
  
  /**
   * Destroy the responsive automation system
   */
  destroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
    
    window.removeEventListener('resize', this.handleResize);
    window.removeEventListener('orientationchange', this.handleResize);
  }
}

// Initialize responsive automation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.responsiveAutomation = new ResponsiveAutomation();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ResponsiveAutomation;
} 