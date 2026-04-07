// components/ErrorBoundary.tsx
// Global error boundary — prevents full app crashes

'use client'

import { Component, ErrorInfo, ReactNode } from 'react'
import { logger } from '@/lib/logger'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    logger.error('ErrorBoundary caught', { 
      error: error.message, 
      componentStack: info.componentStack 
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-[50vh] flex items-center justify-center p-8">
          <div className="text-center space-y-4 max-w-md">
            <div className="text-4xl">⚠️</div>
            <h2 className="text-lg font-semibold text-text-error">Something went wrong</h2>
            <p className="text-sm text-text-dim">
              Your data is safe — this is a display issue
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-kira text-white rounded-lg hover:bg-kira/90 transition-colors text-sm font-medium"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
