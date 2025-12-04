import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "../../lib/utils"

const textareaVariants = cva(
  "flex w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200",
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
        gradient: "border-transparent bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 focus-visible:ring-blue-500",
      },
      size: {
        default: "min-h-[80px]",
        sm: "min-h-[60px] px-2 py-1 text-xs",
        lg: "min-h-[120px] px-4 py-3 text-base",
        xl: "min-h-[160px] px-6 py-4 text-lg",
        compact: "min-h-[60px] px-2 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement>,
    VariantProps<typeof textareaVariants> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <textarea
        className={cn(textareaVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
