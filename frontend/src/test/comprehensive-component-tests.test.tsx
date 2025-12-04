import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Import only basic components that don't need complex contexts
import LoadingSpinner from '../components/LoadingSpinner';
import EnhancedErrorBoundary from '../components/EnhancedErrorBoundary';

// Mock IntersectionObserver
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});

// Mock ResizeObserver
const mockResizeObserver = vi.fn();
mockResizeObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});

describe('Basic Component Tests', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', { value: 1200 }); // Desktop default
    global.IntersectionObserver = mockIntersectionObserver;
    global.ResizeObserver = mockResizeObserver;
    global.fetch = vi.fn();
    
    // Mock localStorage and sessionStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });
    
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic UI Components', () => {
    it('LoadingSpinner renders correctly', () => {
      render(<LoadingSpinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('ErrorBoundary renders without crashing', () => {
      render(
        <EnhancedErrorBoundary>
          <div>Test Content</div>
        </EnhancedErrorBoundary>
      );
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });
  });

  describe('Performance Tests', () => {
    it('Components render within acceptable time', () => {
      const startTime = performance.now();
      
      render(<LoadingSpinner />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      expect(renderTime).toBeLessThan(100); // Should render in under 100ms
    });
  });
});
