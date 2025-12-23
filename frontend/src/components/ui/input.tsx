import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "../../lib/utils"

const inputVariants = cva(
  "flex w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200",
  {
    variants: {
      variant: {
        default: "border-input hover:border-input/80 focus-visible:ring-ring",
        success: "border-green-300 bg-green-50 hover:border-green-400 focus-visible:ring-green-500",
        error: "border-red-300 bg-red-50 hover:border-red-400 focus-visible:ring-red-500",
        warning: "border-yellow-300 bg-yellow-50 hover:border-yellow-400 focus-visible:ring-yellow-500",
        info: "border-blue-300 bg-blue-50 hover:border-blue-400 focus-visible:ring-blue-500",
        ghost: "border-transparent bg-transparent hover:bg-gray-50 focus-visible:ring-gray-500",
        filled: "border-gray-200 bg-gray-50 hover:bg-gray-100 focus-visible:ring-gray-500",
        gradient: "border-gray-200 bg-gray-50 hover:bg-gray-100 focus-visible:ring-gray-500",
      },
      size: {
        default: "h-10",
        sm: "h-8 px-2 text-xs",
        lg: "h-12 px-4 text-base",
        xl: "h-14 px-6 text-lg",
        compact: "h-8 px-2 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, size, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(inputVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
