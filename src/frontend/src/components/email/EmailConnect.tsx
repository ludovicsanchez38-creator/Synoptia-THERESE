/**
 * THÉRÈSE v2 - Email Connect
 *
 * OAuth connection flow for Gmail.
 * Phase 1 Frontend - Email
 */

import { useState } from 'react';
import { Mail, ExternalLink, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

interface EmailConnectProps {
  onSuccess: () => void;
}

export function EmailConnect({ onSuccess }: EmailConnectProps) {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authUrl, setAuthUrl] = useState<string | null>(null);

  async function handleConnect() {
    if (!clientId.trim() || !clientSecret.trim()) {
      setError('Veuillez renseigner les deux champs');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const flow = await api.initiateEmailOAuth(clientId, clientSecret);
      setAuthUrl(flow.auth_url);

      // Open in external browser (Tauri shell)
      try {
        const { open } = await import('@tauri-apps/plugin-shell');
        await open(flow.auth_url);
      } catch {
        window.open(flow.auth_url, '_blank');
      }

      // TODO: Handle callback (需要実装 OAuth callback handler)
      // For now, just show success message
      setTimeout(() => {
        onSuccess();
      }, 2000);
    } catch (err) {
      console.error('Failed to initiate OAuth:', err);
      setError(err instanceof Error ? err.message : 'Échec de la connexion');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-md w-full mx-auto space-y-6 py-4">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mx-auto">
            <Mail className="w-8 h-8 text-accent-cyan" />
          </div>
          <h3 className="text-2xl font-semibold text-text">Connecter Gmail</h3>
          <p className="text-text-muted">
            Pour accéder à vos emails, THÉRÈSE a besoin d'un accès OAuth à votre compte Gmail.
          </p>
        </div>

        {/* Instructions */}
        <div className="p-4 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg space-y-2">
          <p className="text-sm text-text font-medium">Configuration requise :</p>
          <ol className="text-sm text-text-muted space-y-1 list-decimal list-inside">
            <li>
              Créer des credentials OAuth sur{' '}
              <a
                href="https://console.cloud.google.com/apis/credentials"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-cyan hover:underline inline-flex items-center gap-1"
              >
                Google Cloud Console
                <ExternalLink className="w-3 h-3" />
              </a>
            </li>
            <li>Type d'application : "Application de bureau"</li>
            <li>Ajouter l'URI de redirection : http://localhost:8080/oauth/callback</li>
            <li>Copier le Client ID et Client Secret ci-dessous</li>
          </ol>
        </div>

        {/* Form */}
        <div className="space-y-4">
          <div>
            <label className="text-sm text-text-muted mb-2 block">Client ID</label>
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="123456789-abc...apps.googleusercontent.com"
              className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              disabled={loading}
            />
          </div>

          <div>
            <label className="text-sm text-text-muted mb-2 block">Client Secret</label>
            <input
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="GOCSPX-..."
              className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              disabled={loading}
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {authUrl && (
            <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
              <p className="text-sm text-green-400">
                Fenêtre d'autorisation ouverte. Suivez les instructions.
              </p>
            </div>
          )}

          <Button
            variant="primary"
            size="lg"
            onClick={handleConnect}
            disabled={loading || !clientId.trim() || !clientSecret.trim()}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Connexion...
              </>
            ) : (
              <>
                <Mail className="w-4 h-4 mr-2" />
                Connecter Gmail
              </>
            )}
          </Button>
        </div>

        {/* Note */}
        <p className="text-xs text-text-muted text-center">
          Vos identifiants OAuth sont stockés localement et chiffrés.
          <br />
          THÉRÈSE ne les transmet jamais à des tiers.
        </p>
      </div>
    </div>
  );
}
