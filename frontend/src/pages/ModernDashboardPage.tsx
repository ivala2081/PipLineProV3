import React from 'react';
import ModernDashboard from '../components/modern/ModernDashboard';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { UnifiedCard, UnifiedButton, UnifiedBadge } from '../design-system';
import { AlertTriangle } from 'lucide-react';
import { logger } from '../utils/logger';

// Class-based error boundary
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error('ModernDashboard Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
          <div className="max-w-2xl w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-red-500" />
              <h2 className="text-xl font-semibold text-gray-900">Dashboard Error</h2>
            </div>
            <p className="text-gray-600 mb-4">Failed to load Modern Dashboard:</p>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96 whitespace-pre-wrap">
              {this.state.error.message}
              {'\n\n'}
              {this.state.error.stack}
            </pre>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const ModernDashboardPage: React.FC = () => {
  const { t } = useLanguage();
  const { user } = useAuth();

  return (
    <ErrorBoundary>
      <ModernDashboard user={user || undefined} />
    </ErrorBoundary>
  );
};

export default ModernDashboardPage;
