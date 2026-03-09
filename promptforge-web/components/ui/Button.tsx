// components/ui/Button.tsx
// Button component with variants
// 'use client' — interactive component

'use client'

import { ButtonHTMLAttributes, forwardRef } from 'react'

export type ButtonVariant = 'primary' | 'ghost' | 'kira' | 'danger' | 'paid' | 'waitlist'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', size = 'md', children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-kira focus:ring-offset-2 focus:ring-offset-bg disabled:opacity-50 disabled:cursor-not-allowed'
    
    const variantStyles = {
      primary: 'bg-kira text-white hover:bg-kira/90 shadow-kira',
      ghost: 'bg-transparent text-text-default hover:bg-layer2 hover:text-text-bright',
      kira: 'bg-kira text-white hover:bg-kira/90 shadow-kira-strong',
      danger: 'bg-intent text-white hover:bg-intent/90',
      paid: 'bg-engineer text-white hover:bg-engineer/90',
      waitlist: 'bg-layer2 border border-kira text-kira hover:bg-kira hover:text-white',
    }

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
    }

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
