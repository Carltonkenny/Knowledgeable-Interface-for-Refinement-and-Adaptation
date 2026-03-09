// components/ui/Input.tsx
// Input component
// 'use client' — interactive component

'use client'

import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={`w-full px-4 py-2.5 bg-layer2 border border-border-strong rounded-lg text-text-default placeholder:text-text-dim focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'
