import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const formFieldVariants = cva(
  "space-y-2",
  {
    variants: {
      variant: {
        default: "",
        inline: "flex items-center space-x-2 space-y-0",
        stacked: "space-y-2",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface FormFieldProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof formFieldVariants> {
  label?: string
  error?: string
  hint?: string
  required?: boolean
  id?: string
}

const FormField = React.forwardRef<HTMLDivElement, FormFieldProps>(
  ({ className, variant, label, error, hint, required, id, children, ...props }, ref) => {
    const fieldId = id || `field-${Math.random().toString(36).substr(2, 9)}`
    const errorId = error ? `${fieldId}-error` : undefined
    const hintId = hint && !error ? `${fieldId}-hint` : undefined
    const describedBy = [errorId, hintId].filter(Boolean).join(' ') || undefined

    return (
      <div
        ref={ref}
        className={cn(formFieldVariants({ variant, className }))}
        {...props}
      >
        {label && (
          <label 
            htmlFor={fieldId}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {label}
            {required && <span className="text-red-500 ml-1" aria-label="required">*</span>}
          </label>
        )}
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, {
              id: fieldId,
              'aria-invalid': error ? 'true' : undefined,
              'aria-describedby': describedBy,
              'aria-required': required ? 'true' : undefined,
              ...child.props,
            } as any)
          }
          return child
        })}
        {error && (
          <p 
            id={errorId}
            className="text-sm text-red-600 flex items-start gap-1.5 mt-1 animate-in fade-in slide-in-from-top-1 duration-200"
            role="alert"
            aria-live="polite"
          >
            <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </p>
        )}
        {hint && !error && (
          <p 
            id={hintId}
            className="text-sm text-muted-foreground"
          >
            {hint}
          </p>
        )}
      </div>
    )
  }
)
FormField.displayName = "FormField"

export { FormField }
