/**
 * THÉRÈSE v2 - EmailSetupWizard - Configuration SMTP/IMAP
 *
 * Formulaire de saisie des paramètres SMTP/IMAP avec providers pré-configurés.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  AlertCircle,
  Loader2,
  Server,
  Plug,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Button } from '../../ui/Button';
import * as api from '../../../services/api';

interface SmtpConfigStepProps {
  onBack: () => void;
  onSuccess: () => void;
}

interface SmtpFormState {
  email: string;
  password: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  smtp_use_tls: boolean;
}

const DEFAULT_FORM: SmtpFormState = {
  email: '',
  password: '',
  imap_host: '',
  imap_port: 993,
  smtp_host: '',
  smtp_port: 587,
  smtp_use_tls: true,
};

// Ports courants avec leur mode de sécurité conventionnel : choisir un port
// règle aussi la sécurité (un non-technicien ne peut pas déduire SSL direct
// vs STARTTLS depuis « SMTP : 465/587 » - retour Dr_logic-3D, 05/07/2026).
const SMTP_PORT_OPTIONS = [
  { value: 587, label: '587 - STARTTLS (le plus courant)', use_tls: true },
  { value: 465, label: '465 - SSL/TLS direct', use_tls: false },
  { value: 25, label: '25 - non chiffré (rare)', use_tls: false },
];
const IMAP_PORT_OPTIONS = [
  { value: 993, label: '993 - SSL (recommandé)' },
  { value: 143, label: '143 - sans chiffrement' },
];

/** Incohérence port/mode : la cause n°1 des faux « délai de connexion dépassé ». */
function smtpSecurityMismatch(port: number, useTls: boolean): string | null {
  if (port === 465 && useTls) {
    return 'Le port 465 attend une connexion SSL/TLS directe : décoche cette case (ou choisis le port 587).';
  }
  if (port === 587 && !useTls) {
    return 'Le port 587 attend du STARTTLS : coche cette case (ou choisis le port 465).';
  }
  return null;
}

export function SmtpConfigStep({ onBack, onSuccess }: SmtpConfigStepProps) {
  const [form, setForm] = useState<SmtpFormState>(DEFAULT_FORM);
  const [providers, setProviders] = useState<api.EmailProviderConfig[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProviders();
  }, []);

  async function loadProviders() {
    try {
      const list = await api.getEmailProviders();
      setProviders(list);
    } catch {
      // Pas critique, l'utilisateur peut saisir manuellement
    }
  }

  function handleProviderSelect(providerName: string) {
    setSelectedProvider(providerName);
    setTestResult(null);
    setError(null);

    if (providerName === 'custom') {
      setForm((prev) => ({
        ...prev,
        imap_host: '',
        imap_port: 993,
        smtp_host: '',
        smtp_port: 587,
        smtp_use_tls: true,
      }));
      return;
    }

    const provider = providers.find((p) => p.name === providerName);
    if (provider) {
      setForm((prev) => ({
        ...prev,
        imap_host: provider.imap_host,
        imap_port: provider.imap_port,
        smtp_host: provider.smtp_host,
        smtp_port: provider.smtp_port,
        smtp_use_tls: provider.smtp_use_tls,
      }));
    }
  }

  function updateField<K extends keyof SmtpFormState>(key: K, value: SmtpFormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setTestResult(null);
    setError(null);
  }

  const trimmedEmail = form.email.trim();
  const trimmedPassword = form.password.trim();
  const trimmedImapHost = form.imap_host.trim();
  const trimmedSmtpHost = form.smtp_host.trim();
  const hasCredentials = trimmedEmail.length > 0 && trimmedPassword.length > 0;
  const hasServerConfig = trimmedImapHost.length > 0 && trimmedSmtpHost.length > 0;
  const hasValidPorts = form.imap_port > 0 && form.smtp_port > 0;
  const hasCompleteConfiguration = hasCredentials && hasServerConfig && hasValidPorts;
  const canSave = hasCompleteConfiguration;
  const canTest = hasCompleteConfiguration;

  async function handleTest() {
    if (!hasCompleteConfiguration) {
      setError('Remplis tous les champs obligatoires');
      return;
    }

    try {
      setTesting(true);
      setError(null);
      setTestResult(null);
      const result = await api.testSmtpConnection(form);
      setTestResult(result);
    } catch (err: any) {
      // "Failed to fetch" = erreur réseau (backend injoignable, CORS, URL incorrecte)
      if (err instanceof TypeError || err.message === 'Failed to fetch') {
        setError('Impossible de joindre le serveur. Vérifie l\'adresse et le port SMTP.');
      } else if (err?.status === 401 || err?.status === 403) {
        setError('Identifiants incorrects. Vérifie ton adresse email et ton mot de passe.');
      } else if (err?.status === 503 || err?.status === 502) {
        setError('Le serveur SMTP est temporairement indisponible. Réessaie dans quelques instants.');
      } else {
        setError(err.message || 'Échec du test de connexion');
      }
    } finally {
      setTesting(false);
    }
  }

  async function handleSave() {
    if (!hasCompleteConfiguration) {
      setError('Remplis tous les champs obligatoires');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await api.setupSmtpAccount(form);
      onSuccess();
    } catch (err: any) {
      if (err instanceof TypeError || err.message === 'Failed to fetch') {
        setError('Impossible de joindre le serveur. Vérifie l\'adresse et le port SMTP.');
      } else {
        setError(err.message || 'Échec de la configuration');
      }
      setSaving(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-5"
    >
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-[8px] bg-accent-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center mx-auto">
          <Server className="w-6 h-6 text-accent-cyan" />
        </div>
        <h3 className="text-lg font-semibold text-text">Configuration SMTP/IMAP</h3>
        <p className="text-sm text-text-muted">
          Configure ton compte email pour envoyer et recevoir des messages
        </p>
      </div>

      {/* Provider selector */}
      {providers.length > 0 && (
        <div className="space-y-1.5">
          <label htmlFor="smtp-provider" className="text-sm text-text-muted">Fournisseur email</label>
          <select
            id="smtp-provider"
            value={selectedProvider}
            onChange={(e) => handleProviderSelect(e.target.value)}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          >
            <option value="">Sélectionner un fournisseur...</option>
            {providers.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
            <option value="custom">Autre (configuration manuelle)</option>
          </select>
        </div>
      )}

      {/* Email + Password */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <label htmlFor="smtp-email" className="text-sm text-text-muted">Adresse email *</label>
          <input
            id="smtp-email"
            type="email"
            value={form.email}
            onChange={(e) => updateField('email', e.target.value)}
            placeholder="toi@exemple.fr"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="smtp-password" className="text-sm text-text-muted">Mot de passe / App password *</label>
          <div className="relative">
            <input
              id="smtp-password"
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={(e) => updateField('password', e.target.value)}
              placeholder="Mot de passe applicatif"
              className="w-full px-3 py-2 pr-11 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            />
            <button
              type="button"
              aria-controls="smtp-password"
              aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
              aria-pressed={showPassword}
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute inset-y-0 right-0 px-3 text-text-muted transition-colors hover:text-text"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* IMAP Config */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <label htmlFor="smtp-imap-host" className="text-sm text-text-muted">Serveur IMAP *</label>
          <input
            id="smtp-imap-host"
            type="text"
            value={form.imap_host}
            onChange={(e) => updateField('imap_host', e.target.value)}
            placeholder="imap.exemple.fr"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="smtp-imap-port" className="text-sm text-text-muted">Port IMAP</label>
          <select
            id="smtp-imap-port"
            value={IMAP_PORT_OPTIONS.some((o) => o.value === form.imap_port) ? String(form.imap_port) : 'custom'}
            onChange={(e) => {
              if (e.target.value !== 'custom') updateField('imap_port', parseInt(e.target.value));
            }}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          >
            {IMAP_PORT_OPTIONS.map((o) => (
              <option key={o.value} value={String(o.value)}>{o.label}</option>
            ))}
            <option value="custom">Autre : {form.imap_port}</option>
          </select>
        </div>
      </div>

      {/* SMTP Config */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <label htmlFor="smtp-smtp-host" className="text-sm text-text-muted">Serveur SMTP *</label>
          <input
            id="smtp-smtp-host"
            type="text"
            value={form.smtp_host}
            onChange={(e) => updateField('smtp_host', e.target.value)}
            placeholder="smtp.exemple.fr"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="smtp-smtp-port" className="text-sm text-text-muted">Port SMTP</label>
          <select
            id="smtp-smtp-port"
            value={SMTP_PORT_OPTIONS.some((o) => o.value === form.smtp_port) ? String(form.smtp_port) : 'custom'}
            onChange={(e) => {
              if (e.target.value === 'custom') return;
              const option = SMTP_PORT_OPTIONS.find((o) => String(o.value) === e.target.value);
              if (option) {
                // Choisir un port courant règle aussi le mode de sécurité.
                setForm((prev) => ({ ...prev, smtp_port: option.value, smtp_use_tls: option.use_tls }));
                setTestResult(null);
                setError(null);
              }
            }}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          >
            {SMTP_PORT_OPTIONS.map((o) => (
              <option key={o.value} value={String(o.value)}>{o.label}</option>
            ))}
            <option value="custom">Autre : {form.smtp_port}</option>
          </select>
        </div>
      </div>

      {/* TLS toggle */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={form.smtp_use_tls}
          onChange={(e) => updateField('smtp_use_tls', e.target.checked)}
          className="w-4 h-4 rounded border-border/50 bg-background/60 text-accent-cyan focus:ring-accent-cyan/50"
        />
        <span className="text-sm text-text-muted">Utiliser TLS/STARTTLS (587) - décocher pour le SSL direct (465)</span>
      </label>

      {/* Incohérence port/mode : dite AVANT le test, au lieu d'un faux timeout après */}
      {smtpSecurityMismatch(form.smtp_port, form.smtp_use_tls) && (
        <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-warning mt-0.5 shrink-0" />
            <span className="text-sm text-warning">
              {smtpSecurityMismatch(form.smtp_port, form.smtp_use_tls)}
            </span>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            <span className="text-sm text-red-400">{error}</span>
          </div>
        </div>
      )}

      {/* Test result */}
      {testResult && (
        <div
          className={`p-3 rounded-lg border ${
            testResult.success
              ? 'bg-green-500/10 border-green-500/20'
              : 'bg-red-500/10 border-red-500/20'
          }`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-400" />
            )}
            <span
              className={`text-sm ${testResult.success ? 'text-green-400' : 'text-red-400'}`}
            >
              {testResult.message}
            </span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-2">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          Retour
        </Button>

        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleTest}
            disabled={!canTest || testing}
          >
            {testing ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Plug className="w-4 h-4 mr-1" />
            )}
            Tester
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={!canSave || saving}
          >
            {saving ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <ArrowRight className="w-4 h-4 mr-1" />
            )}
            Enregistrer
          </Button>
        </div>
      </div>

      <p className="text-xs text-text-muted text-center">
        Le mot de passe est chiffré localement (Fernet AES-128). Utilise un mot de passe d'application si ton fournisseur le supporte.
      </p>
    </motion.div>
  );
}
