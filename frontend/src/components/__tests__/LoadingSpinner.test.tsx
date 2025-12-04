import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LoadingSpinner from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders without crashing', () => {
    render(<LoadingSpinner />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })


  it('displays the loading message', () => {
    const message = 'Custom loading message'
    render(<LoadingSpinner message={message} />)
    expect(screen.getByText(message)).toBeInTheDocument()
  })

  it('applies custom size classes', () => {
    render(<LoadingSpinner size="lg" />)
    const spinnerElement = screen.getByRole('status').querySelector('.animate-spin')
    expect(spinnerElement).toHaveClass('h-12', 'w-12')
  })

  it('applies fullScreen class when specified', () => {
    render(<LoadingSpinner fullScreen={true} />)
    const container = screen.getByRole('status')
    expect(container).toHaveClass('min-h-screen')
  })

  it('applies custom className', () => {
    const customClass = 'custom-class'
    render(<LoadingSpinner className={customClass} />)
    const container = screen.getByRole('status')
    expect(container).toHaveClass(customClass)
  })
}) 