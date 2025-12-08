// Button Component Tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen, userEvent } from '@/test/utils/test-utils'

// Mock Button component (adjust import based on your actual component)
function Button({ 
  children, 
  onClick, 
  disabled = false, 
  variant = 'primary' 
}: { 
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary' | 'danger'
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {children}
    </button>
  )
}

describe('Button Component', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<Button onClick={handleClick}>Click me</Button>)
    
    await user.click(screen.getByText('Click me'))
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(
      <Button onClick={handleClick} disabled>
        Click me
      </Button>
    )
    
    const button = screen.getByText('Click me')
    expect(button).toBeDisabled()
    
    await user.click(button)
    
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('applies correct variant class', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByText('Primary')).toHaveClass('btn-primary')
    
    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByText('Secondary')).toHaveClass('btn-secondary')
    
    rerender(<Button variant="danger">Danger</Button>)
    expect(screen.getByText('Danger')).toHaveClass('btn-danger')
  })
})

