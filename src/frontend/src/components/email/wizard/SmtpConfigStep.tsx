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

export function SmtpConfigStep({ onBack, onSuccess }: SmtpConfigStepProps) {
  const [form, setForm] = useState<SmtpFormState>(DEFAULT_FORM);
  const [providers, setProviders] = useState<api.EmailProviderConfig[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
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

  async function handleTest() {
    if (!form.email || !form.password || !form.imap_host || !form.smtp_host) {
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
      setError(err.message || 'Échec du test de connexion');
    } finally {
      setTesting(false);
    }
  }

  async function handleSave() {
    try {
      setSaving(true);
      setError(null);
      await api.setupSmtpAccount(form);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Échec de la configuration');
      setSaving(false);
    }
  }

  const isFormValid = form.email && form.password && form.imap_host && form.smtp_host;

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-5"
    >
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mx-auto">
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
          <label className="text-sm text-text-muted">Fournisseur email</label>
          <select
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
          <label className="text-sm text-text-muted">Adresse email *</label>
          <input
            type="email"
            value={form.email}
            onChange={(e) => updateField('email', e.target.value)}
            placeholder="toi@exemple.fr"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm text-text-muted">Mot de passe / App password *</label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => updateField('password', e.target.value)}
            placeholder="Mot de passe applicatif"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
      </div>

      {/* IMAP Config */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <label className="text-sm text-text-muted">Serveur IMAP *</label>
          <input
            type="text"
            value={form.imap_host}
            onChange={(e) => updateField('imap_host', e.target.value)}
            placeholder="imap.exemple.fr"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm text-text-muted">Port IMAP</label>
          <input
            type="number"
            value={form.imap_port}
            onChange={(e) => updateField('imap_port', parseInt(e.target.value) || 993)}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
      </div>

      {/* SMTP Config */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <label className="text-sm text-text-muted">Serveur SMTP *</label>
          <input
            type="text"
            value={form.smtp_host}
            onChange={(e) => updateField('smtp_host', e.target.value)}
            placeholder="smtp.exemple.fr"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm text-text-muted">Port SMTP</label>
          <input
            type="number"
            value={form.smtp_port}
            onChange={(e) => updateField('smtp_port', parseInt(e.target.value) || 587)}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
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
        <span className="text-sm text-text-muted">Utiliser TLS/STARTTLS (recommandé)</span>
      </label>

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
            disabled={!isFormValid || testing}
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
            disabled={!isFormValid || saving}
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
