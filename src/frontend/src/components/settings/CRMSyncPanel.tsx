/**
 * THÉRÈSE v2 - CRM Sync Panel
 *
 * UI for syncing CRM data from Google Sheets.
 * Supports OAuth and API key authentication.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { RefreshCw, Link2, Check, AlertCircle, Loader2, ExternalLink, Cloud, Key, Upload } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

interface CRMSyncPanelProps {
  onSyncComplete?: () => void;
}

// Default Synoptia CRM spreadsheet ID
const DEFAULT_SPREADSHEET_ID = '1gXhiy43tvaDW0Y9FEGPmfB7BBCbUCOl_Xb6nkWtnnUk';

export function CRMSyncPanel({ onSyncComplete }: CRMSyncPanelProps) {
  const [config, setConfig] = useState<api.CRMSyncConfig | null>(null);
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [lastSyncStats, setLastSyncStats] = useState<api.CRMSyncStats | null>(null);
  const [spreadsheetId, setSpreadsheetId] = useState(DEFAULT_SPREADSHEET_ID);

  // F-13 : formulaire re-saisie credentials Google OAuth
  const [showCredentialsForm, setShowCredentialsForm] = useState(false);
  const [clientIdInput, setClientIdInput] = useState('');
  const [clientSecretInput, setClientSecretInput] = useState('');
  const [credentialsSaving, setCredentialsSaving] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const credentialsFileRef = useRef<HTMLInputElement>(null);

  // F-16 : Importer credentials.json
  const handleImportCredentials = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportError(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        const creds = json.installed || json.web;
        if (!creds?.client_id || !creds?.client_secret) {
          setImportError('Format invalide : client_id ou client_secret introuvable');
          return;
        }
        setClientIdInput(creds.client_id);
        setClientSecretInput(creds.client_secret);
        setImportError(null);
      } catch {
        setImportError('Fichier JSON invalide');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  }, []);

  // Load config on mount
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const [cfg, keys] = await Promise.all([
        api.getCRMSyncConfig(),
        api.getApiKeys().catch(() => ({})),
      ]);
      setConfig(cfg);
      setApiKeys(keys);
      if (cfg.spreadsheet_id) {
        setSpreadsheetId(cfg.spreadsheet_id);
      }
    } catch (err) {
      console.error('Failed to load CRM config:', err);
      setError('Impossible de charger la configuration CRM');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSpreadsheetId = async () => {
    if (!spreadsheetId.trim()) {
      setError('Veuillez entrer un ID de spreadsheet');
      return;
    }

    try {
      setError(null);
      const cfg = await api.setCRMSpreadsheetId(spreadsheetId.trim());
      setConfig(cfg);
      setSuccess('Spreadsheet configuré');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to save spreadsheet ID:', err);
      setError('Impossible de sauvegarder le spreadsheet ID');
    }
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      setError(null);
      const result = await api.initiateCRMOAuth();

      // Open auth URL in browser (Tauri shell pour ouvrir le navigateur externe)
      try {
        const { open } = await import('@tauri-apps/plugin-shell');
        await open(result.auth_url);
      } catch {
        window.open(result.auth_url, '_blank');
      }

      setSuccess('Autorisez l\'accès dans le navigateur...');

      // Polling : détecter quand le callback OAuth est terminé
      let attempts = 0;
      const maxAttempts = 40; // 2 minutes (3s x 40)
      const pollInterval = setInterval(async () => {
        attempts++;
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          setConnecting(false);
          return;
        }
        try {
          const cfg = await api.getCRMSyncConfig();
          if (cfg.has_token) {
            clearInterval(pollInterval);
            setConfig(cfg);
            if (cfg.spreadsheet_id) {
              setSpreadsheetId(cfg.spreadsheet_id);
              setSuccess('Google Sheets connecté et CRM créé automatiquement');
            } else {
              setSuccess('Google Sheets connecté avec succès');
            }
            setConnecting(false);
          }
        } catch {
          // Ignorer les erreurs de polling
        }
      }, 3000);
    } catch (err: any) {
      console.error('Failed to initiate OAuth:', err);
      const msg = err.message || 'Impossible de lancer la connexion OAuth';
      setError(msg);
      setConnecting(false);
      // F-13 : si Bad Request (credentials introuvables/corrompues), proposer la re-saisie
      if (msg.includes('introuvables') || msg.includes('Bad Request') || (err.status && err.status === 400)) {
        setShowCredentialsForm(true);
      }
    }
  };

  // F-13 : sauvegarde des credentials Google OAuth
  const handleSaveCredentials = async () => {
    if (!clientIdInput.trim() || !clientSecretInput.trim()) {
      setError('Les deux champs sont requis');
      return;
    }
    setCredentialsSaving(true);
    setError(null);
    try {
      await api.saveCRMGoogleCredentials(clientIdInput.trim(), clientSecretInput.trim());
      setSuccess('Credentials Google OAuth enregistrées');
      setShowCredentialsForm(false);
      setClientIdInput('');
      setClientSecretInput('');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la sauvegarde des credentials');
    } finally {
      setCredentialsSaving(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSuccess(null);

      const result = await api.syncCRM();

      if (result.success) {
        setSuccess(result.message);
        setLastSyncStats(result.stats);
        onSyncComplete?.();
      } else {
        setError(result.message);
        if (result.stats?.errors?.length) {
          setError(`${result.message}\n${result.stats.errors.join('\n')}`);
        }
      }

      // Refresh config to get updated last_sync
      await loadConfig();
    } catch (err: any) {
      console.error('CRM sync failed:', err);
      setError(err.message || 'Erreur de synchronisation');
    } finally {
      setSyncing(false);
    }
  };

  // Check if we have any auth method available
  const hasAuthMethod = config?.has_token || apiKeys.has_gemini_key;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500/20 to-emerald-500/20 flex items-center justify-center">
          <Cloud className="w-5 h-5 text-green-400" />
        </div>
        <div>
          <h3 className="font-medium text-text">Synchronisation CRM</h3>
          <p className="text-xs text-text-muted">
            Importer les contacts et projets depuis Google Sheets
          </p>
        </div>
      </div>

      {/* Error/Success messages */}
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
            <span className="text-sm text-red-400 whitespace-pre-line">{error}</span>
          </div>
        </div>
      )}

      {success && (
        <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-green-400" />
            <span className="text-sm text-green-400">{success}</span>
          </div>
        </div>
      )}

      {/* Spreadsheet ID configuration */}
      <div className="space-y-2">
        <label className="text-sm text-text-muted">ID du Google Spreadsheet CRM</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={spreadsheetId}
            onChange={(e) => setSpreadsheetId(e.target.value)}
            placeholder="ID du spreadsheet (ex: 1gXhiy43...)"
            className="flex-1 px-3 py-2 bg-surface border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSaveSpreadsheetId}
            disabled={!spreadsheetId.trim() || spreadsheetId === config?.spreadsheet_id}
          >
            Enregistrer
          </Button>
        </div>
        <p className="text-xs text-text-muted">
          L'ID se trouve dans l'URL du spreadsheet : docs.google.com/spreadsheets/d/<span className="text-accent-cyan">ID_ICI</span>/edit
        </p>
      </div>

      {/* Auth status */}
      <div className="p-3 bg-background/40 rounded-lg border border-border/30 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text">Authentification</span>
          {hasAuthMethod ? (
            <span className="text-xs text-green-400 flex items-center gap-1">
              <Check className="w-3 h-3" /> Disponible
            </span>
          ) : (
            <span className="text-xs text-yellow-400">Non configurée</span>
          )}
        </div>

        {/* Auth methods status */}
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            {config?.has_token ? (
              <Check className="w-3 h-3 text-green-400" />
            ) : (
              <Link2 className="w-3 h-3 text-text-muted" />
            )}
            <span className={config?.has_token ? 'text-green-400' : 'text-text-muted'}>
              OAuth Google Sheets
            </span>
          </div>
          <div className="flex items-center gap-2">
            {apiKeys.has_gemini_key ? (
              <Check className="w-3 h-3 text-green-400" />
            ) : (
              <Key className="w-3 h-3 text-text-muted" />
            )}
            <span className={apiKeys.has_gemini_key ? 'text-green-400' : 'text-text-muted'}>
              Clé API Gemini (fallback)
            </span>
          </div>
        </div>

        {/* Connect/Reconnect button */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleConnect}
          disabled={connecting}
          className="w-full mt-2"
        >
          {connecting ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <ExternalLink className="w-4 h-4 mr-2" />
          )}
          {config?.has_token ? 'Reconnecter Google Sheets' : 'Connecter Google Sheets'}
        </Button>
      </div>

      {/* F-13 : formulaire re-saisie credentials Google OAuth */}
      {showCredentialsForm && (
        <div className="p-3 bg-background/40 rounded-lg border border-border/30 space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="text-sm font-medium text-text">Credentials Google OAuth</h4>
              <p className="text-xs text-text-muted mt-1">
                Créez un projet sur{' '}
                <a
                  href="https://console.cloud.google.com/apis/credentials"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-cyan hover:underline"
                >
                  Google Cloud Console
                </a>
                {' '}et importez le fichier <code className="text-accent-cyan">credentials.json</code>.
              </p>
            </div>
            <input
              ref={credentialsFileRef}
              type="file"
              accept=".json"
              onChange={handleImportCredentials}
              className="hidden"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => credentialsFileRef.current?.click()}
              className="shrink-0 ml-2"
            >
              <Upload className="w-4 h-4 mr-1.5" />
              Importer
            </Button>
          </div>
          {importError && (
            <p className="text-xs text-red-400">{importError}</p>
          )}
          <div className="space-y-2">
            <div>
              <label className="text-xs text-text-muted">Client ID</label>
              <input
                type="text"
                value={clientIdInput}
                onChange={(e) => setClientIdInput(e.target.value)}
                placeholder="...apps.googleusercontent.com"
                className="w-full mt-1 px-3 py-2 bg-surface border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Client Secret</label>
              <input
                type="password"
                value={clientSecretInput}
                onChange={(e) => setClientSecretInput(e.target.value)}
                placeholder="GOCSPX-..."
                className="w-full mt-1 px-3 py-2 bg-surface border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 font-mono"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={handleSaveCredentials}
              disabled={credentialsSaving || !clientIdInput.trim() || !clientSecretInput.trim()}
              className="flex-1"
            >
              {credentialsSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Enregistrer'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowCredentialsForm(false)}
            >
              Annuler
            </Button>
          </div>
        </div>
      )}

      {/* Last sync info */}
      {config?.last_sync && (
        <div className="p-3 bg-background/40 rounded-lg border border-border/30">
          <p className="text-xs text-text-muted">
            Dernière synchronisation : {new Date(config.last_sync).toLocaleString('fr-FR')}
          </p>
        </div>
      )}

      {/* Sync stats */}
      {lastSyncStats && lastSyncStats.total_synced > 0 && (
        <div className="grid grid-cols-3 gap-2">
          <div className="p-2 bg-background/40 rounded-lg border border-border/30 text-center">
            <p className="text-lg font-bold text-text">
              {lastSyncStats.contacts_created + lastSyncStats.contacts_updated}
            </p>
            <p className="text-xs text-text-muted">Contacts</p>
          </div>
          <div className="p-2 bg-background/40 rounded-lg border border-border/30 text-center">
            <p className="text-lg font-bold text-text">
              {lastSyncStats.projects_created + lastSyncStats.projects_updated}
            </p>
            <p className="text-xs text-text-muted">Projets</p>
          </div>
          <div className="p-2 bg-background/40 rounded-lg border border-border/30 text-center">
            <p className="text-lg font-bold text-text">
              {lastSyncStats.deliverables_created + lastSyncStats.deliverables_updated}
            </p>
            <p className="text-xs text-text-muted">Livrables</p>
          </div>
        </div>
      )}

      {/* Sync button */}
      <Button
        variant="primary"
        onClick={handleSync}
        disabled={syncing || !config?.spreadsheet_id || !hasAuthMethod}
        className="w-full"
      >
        {syncing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Synchronisation en cours...
          </>
        ) : (
          <>
            <RefreshCw className="w-4 h-4 mr-2" />
            Synchroniser maintenant
          </>
        )}
      </Button>

      {/* Help text */}
      <p className="text-xs text-text-muted text-center">
        La synchronisation importe les Clients, Projets et Livrables depuis le CRM Google Sheets.
        Google Sheets reste la source de vérité.
      </p>
    </div>
  );
}
