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
  Server,
  Plug,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Button } from '../../ui/Button';
import * as api from '../../../services/api';
import { Spinner } from '../../ui/Spinner';
import { Alerte } from '../../ui/Alerte';
import { FormField } from '../../ui/FormField';
import { Input } from '../../ui/Input';
import { Select } from '../../ui/Select';

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
  /** D79 : « Autre » ouvre un champ numérique au lieu d'être ignoré. */
  const [portsPersonnalises, setPortsPersonnalises] = useState({ imap: false, smtp: false });

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
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent-tint">
          <Server className="w-6 h-6 text-accent-cyan-ink" />
        </div>
        <h3 className="text-lg font-semibold text-text">Configuration SMTP/IMAP</h3>
        <p className="text-sm text-text-muted">
          Configure ton compte email pour envoyer et recevoir des messages
        </p>
      </div>

      {/* Provider selector */}
      {providers.length > 0 && (
        <FormField label="Fournisseur email" htmlFor="smtp-provider">
          <Select
            id="smtp-provider"
            value={selectedProvider}
            onChange={(e) => handleProviderSelect(e.target.value)}
            placeholder="Sélectionner un fournisseur..."
            options={[
              ...providers.map((provider) => ({ value: provider.name, label: provider.name })),
              { value: 'custom', label: 'Autre (configuration manuelle)' },
            ]}
          />
        </FormField>
      )}

      {/* Email + Password */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <FormField label="Adresse email" htmlFor="smtp-email" required>
          <Input
            id="smtp-email"
            type="email"
            aria-label="Adresse email *"
            value={form.email}
            onChange={(e) => updateField('email', e.target.value)}
            placeholder="toi@exemple.fr"
          />
        </FormField>
        <FormField label="Mot de passe / App password" htmlFor="smtp-password" required>
          <div className="relative">
            <Input
              id="smtp-password"
              type={showPassword ? 'text' : 'password'}
              aria-label="Mot de passe / App password *"
              value={form.password}
              onChange={(e) => updateField('password', e.target.value)}
              placeholder="Mot de passe applicatif"
              className="pr-11"
            />
            <Button
              variant="ghost"
              size="icon"
              type="button"
              aria-controls="smtp-password"
              aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
              aria-pressed={showPassword}
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute inset-y-0 right-0"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
          </div>
        </FormField>
      </div>

      {/* IMAP Config */}
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Serveur IMAP" htmlFor="smtp-imap-host" required>
          <Input
            id="smtp-imap-host"
            type="text"
            aria-label="Serveur IMAP *"
            value={form.imap_host}
            onChange={(e) => updateField('imap_host', e.target.value)}
            placeholder="imap.exemple.fr"
          />
        </FormField>
        <FormField label="Port IMAP" htmlFor="smtp-imap-port">
          <Select
            id="smtp-imap-port"
            value={!portsPersonnalises.imap && IMAP_PORT_OPTIONS.some((o) => o.value === form.imap_port) ? String(form.imap_port) : 'custom'}
            onChange={(e) => {
              if (e.target.value === 'custom') {
                setPortsPersonnalises((p) => ({ ...p, imap: true }));
                return;
              }
              setPortsPersonnalises((p) => ({ ...p, imap: false }));
              updateField('imap_port', parseInt(e.target.value));
            }}
            options={[
              ...IMAP_PORT_OPTIONS.map((option) => ({ value: String(option.value), label: option.label })),
              { value: 'custom', label: `Autre : ${form.imap_port}` },
            ]}
          />
          {(portsPersonnalises.imap || !IMAP_PORT_OPTIONS.some((o) => o.value === form.imap_port)) && (
            <Input
              id="smtp-imap-port-custom"
              type="number"
              min={1}
              max={65535}
              aria-label="Port IMAP personnalisé"
              value={form.imap_port}
              onChange={(e) => updateField('imap_port', parseInt(e.target.value) || 0)}
              className="mt-1.5"
            />
          )}
        </FormField>
      </div>

      {/* SMTP Config */}
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Serveur SMTP" htmlFor="smtp-smtp-host" required>
          <Input
            id="smtp-smtp-host"
            type="text"
            aria-label="Serveur SMTP *"
            value={form.smtp_host}
            onChange={(e) => updateField('smtp_host', e.target.value)}
            placeholder="smtp.exemple.fr"
          />
        </FormField>
        <FormField label="Port SMTP" htmlFor="smtp-smtp-port">
          <Select
            id="smtp-smtp-port"
            value={!portsPersonnalises.smtp && SMTP_PORT_OPTIONS.some((o) => o.value === form.smtp_port) ? String(form.smtp_port) : 'custom'}
            onChange={(e) => {
              if (e.target.value === 'custom') {
                setPortsPersonnalises((p) => ({ ...p, smtp: true }));
                return;
              }
              setPortsPersonnalises((p) => ({ ...p, smtp: false }));
              const option = SMTP_PORT_OPTIONS.find((o) => String(o.value) === e.target.value);
              if (option) {
                // Choisir un port courant règle aussi le mode de sécurité.
                setForm((prev) => ({ ...prev, smtp_port: option.value, smtp_use_tls: option.use_tls }));
                setTestResult(null);
                setError(null);
              }
            }}
            options={[
              ...SMTP_PORT_OPTIONS.map((option) => ({ value: String(option.value), label: option.label })),
              { value: 'custom', label: `Autre : ${form.smtp_port}` },
            ]}
          />
          {(portsPersonnalises.smtp || !SMTP_PORT_OPTIONS.some((o) => o.value === form.smtp_port)) && (
            <Input
              id="smtp-smtp-port-custom"
              type="number"
              min={1}
              max={65535}
              aria-label="Port SMTP personnalisé"
              value={form.smtp_port}
              onChange={(e) => updateField('smtp_port', parseInt(e.target.value) || 0)}
              className="mt-1.5"
            />
          )}
        </FormField>
      </div>

      {/* TLS toggle */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={form.smtp_use_tls}
          onChange={(e) => updateField('smtp_use_tls', e.target.checked)}
          className="w-4 h-4 rounded-sm border-border/50 bg-background/60 text-accent-cyan-ink focus:ring-ring/50"
        />
        <span className="text-sm text-text-muted">Utiliser TLS/STARTTLS (587) - décocher pour le SSL direct (465)</span>
      </label>

      {/* Incohérence port/mode : dite AVANT le test, au lieu d'un faux timeout après */}
      {smtpSecurityMismatch(form.smtp_port, form.smtp_use_tls) && (
        <Alerte ton="attention" icone={<AlertCircle className="h-4 w-4 text-warning" />}>
          {smtpSecurityMismatch(form.smtp_port, form.smtp_use_tls)}
        </Alerte>
      )}

      {/* Error */}
      {error && (
        <Alerte icone={<AlertCircle className="h-4 w-4 text-error" />}>{error}</Alerte>
      )}

      {/* Test result */}
      {testResult && (
        <div
          className={`rounded-md border p-3 ${
            testResult.success
              ? 'bg-[var(--color-success-tint)] border-success/30'
              : 'bg-[var(--color-error-tint)] border-error/30'
          }`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? (
              <Check className="w-4 h-4 text-success" />
            ) : (
              <AlertCircle className="w-4 h-4 text-error" />
            )}
            <span
              className={`text-sm ${testResult.success ? 'text-success' : 'text-error'}`}
            >
              {testResult.message}
            </span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 max-[840px]:items-stretch">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          Retour
        </Button>

        <div className="flex flex-wrap gap-2 max-[840px]:basis-full">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleTest}
            disabled={!canTest || testing}
          >
            {testing ? (
              <Spinner taille="bouton" className="mr-1" />
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
              <Spinner taille="bouton" className="mr-1" />
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
