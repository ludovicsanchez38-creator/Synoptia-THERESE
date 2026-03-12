import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary global - attrape les erreurs React non capturées
 * pour éviter l'écran blanc et proposer un rechargement propre.
 */
export class GlobalErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[GlobalErrorBoundary] Erreur non capturée :', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="h-screen w-screen flex items-center justify-center"
          style={{ backgroundColor: '#0B1226', color: '#E6EDF7' }}
        >
          <div className="text-center max-w-md px-6">
            <h1
              className="text-4xl font-bold mb-4"
              style={{ color: '#22D3EE' }}
            >
              Oups
            </h1>
            <p className="text-lg mb-2">
              Une erreur inattendue s'est produite.
            </p>
            <p className="text-sm mb-6" style={{ color: '#B6C7DA' }}>
              L'application a rencontré un problème. Vous pouvez relancer pour reprendre.
            </p>
            {this.state.error && (
              <pre
                className="text-xs text-left mb-6 p-3 rounded-lg overflow-auto max-h-32"
                style={{ backgroundColor: '#131B35', color: '#B6C7DA' }}
              >
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReload}
              className="px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200"
              style={{
                backgroundColor: '#22D3EE',
                color: '#0B1226',
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLButtonElement).style.opacity = '0.85';
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLButtonElement).style.opacity = '1';
              }}
            >
              Relancer l'application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
