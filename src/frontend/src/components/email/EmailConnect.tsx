/**
 * THÉRÈSE v2 - Email Connect
 *
 * OAuth connection flow for Gmail.
 * Phase 1 Frontend - Email
 */

import { useState } from 'react';
import { Mail, ExternalLink, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { Carte } from '../ui/Carte';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';

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
      setError('Renseigne les deux champs');
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
      <Carte className="mx-auto w-full max-w-md space-y-6 p-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-accent-tint">
            <Mail className="h-8 w-8 text-accent" />
          </div>
          <h3 className="text-2xl font-semibold text-text">Connecter Gmail</h3>
          <p className="text-text-muted">
            Pour accéder à tes emails, THÉRÈSE a besoin d'un accès OAuth à ton compte Gmail.
          </p>
        </div>

        {/* Instructions */}
        <div className="space-y-2 rounded-md border border-border bg-surface-2 p-4">
          <p className="text-sm text-text font-medium">Configuration requise :</p>
          <ol className="text-sm text-text-muted space-y-1 list-decimal list-inside">
            <li>
              Créer des credentials OAuth sur{' '}
              <a
                href="https://console.cloud.google.com/apis/credentials"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-cyan-ink hover:underline inline-flex items-center gap-1"
              >
                Google Cloud Console
                <ExternalLink className="w-3 h-3" />
              </a>
            </li>
            <li>Type d'application : "Application Web"</li>
            <li>Ajouter l'URI de redirection : http://localhost:8080/oauth/callback</li>
            <li>Copier l'ID client et le Code secret du client ci-dessous</li>
          </ol>
        </div>

        {/* Form */}
        <div className="space-y-4">
          <FormField label="ID client" htmlFor="emailconnect-id-client">
            <Input id="emailconnect-id-client"
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="123456789-abc...apps.googleusercontent.com"
              disabled={loading}
            />
          </FormField>

          <FormField label="Code secret du client" htmlFor="emailconnect-code-secret-du-client">
            <Input id="emailconnect-code-secret-du-client"
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="GOCSPX-..."
              disabled={loading}
            />
          </FormField>

          {error && (
            <Alerte icone={<AlertCircle className="h-4 w-4 text-error" />}>{error}</Alerte>
          )}

          {authUrl && (
            <div role="status" className="flex items-center gap-2 rounded-md border border-success/30 bg-[var(--color-success-tint)] p-3">
              <p className="text-sm text-success">
                Fenêtre d'autorisation ouverte. Suis les instructions.
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
                <Spinner taille="bouton" className="mr-2" />
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
          Tes identifiants OAuth sont stockés localement et chiffrés.
          <br />
          THÉRÈSE ne les transmet jamais à des tiers.
        </p>
      </Carte>
    </div>
  );
}
