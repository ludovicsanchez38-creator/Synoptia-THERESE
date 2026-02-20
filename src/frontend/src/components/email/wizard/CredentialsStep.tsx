/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 3
 *
 * Saisie des identifiants avec validation temps réel.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Key, ChevronLeft, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '../../ui/Button';
import * as api from '../../../services/api';

interface CredentialsStepProps {
  clientId: string;
  clientSecret: string;
  onChange: (field: 'clientId' | 'clientSecret', value: string) => void;
  onBack: () => void;
  onContinue: () => void;
}

interface ValidationState {
  clientId: { valid: boolean; message: string } | null;
  clientSecret: { valid: boolean; message: string } | null;
}

export function CredentialsStep({
  clientId,
  clientSecret,
  onChange,
  onBack,
  onContinue,
}: CredentialsStepProps) {
  const [validation, setValidation] = useState<ValidationState>({
    clientId: null,
    clientSecret: null,
  });
  const [validating, setValidating] = useState(false);

  // Validation temps réel (debounced)
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (clientId.trim() && clientSecret.trim()) {
        setValidating(true);
        try {
          const result = await api.validateEmailCredentials(clientId, clientSecret);
          setValidation({
            clientId: {
              valid: result.client_id.valid,
              message: result.client_id.message,
            },
            clientSecret: {
              valid: result.client_secret.valid,
              message: result.client_secret.message,
            },
          });
        } catch (error) {
          console.error('Validation failed:', error);
        } finally {
          setValidating(false);
        }
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [clientId, clientSecret]);

  const allValid =
    validation.clientId?.valid === true && validation.clientSecret?.valid === true;

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mx-auto mb-2">
          <Key className="w-6 h-6 text-accent-cyan" />
        </div>
        <h3 className="text-lg font-semibold text-text">Entre tes identifiants</h3>
        <p className="text-sm text-text-muted">
          Copie l'ID client et le Code secret du client depuis Google Cloud Console
        </p>
      </div>

      {/* ID client */}
      <div>
        <label htmlFor="clientId" className="text-sm text-text-muted mb-2 block">
          ID client
        </label>
        <div className="relative">
          <input
            id="clientId"
            type="text"
            value={clientId}
            onChange={(e) => onChange('clientId', e.target.value)}
            placeholder="123456789-abc...apps.googleusercontent.com"
            className="w-full px-4 py-3 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
          {validation.clientId && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {validation.clientId.valid ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-400" />
              )}
            </div>
          )}
        </div>
        {validation.clientId && (
          <p
            className={`text-xs mt-1 ${
              validation.clientId.valid ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {validation.clientId.message}
          </p>
        )}
      </div>

      {/* Code secret du client */}
      <div>
        <label htmlFor="clientSecret" className="text-sm text-text-muted mb-2 block">
          Code secret du client
        </label>
        <div className="relative">
          <input
            id="clientSecret"
            type="password"
            value={clientSecret}
            onChange={(e) => onChange('clientSecret', e.target.value)}
            placeholder="GOCSPX-..."
            className="w-full px-4 py-3 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
          {validation.clientSecret && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {validation.clientSecret.valid ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-400" />
              )}
            </div>
          )}
        </div>
        {validation.clientSecret && (
          <p
            className={`text-xs mt-1 ${
              validation.clientSecret.valid ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {validation.clientSecret.message}
          </p>
        )}
      </div>

      {/* Info */}
      <div className="p-4 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
        <p className="text-sm text-text-muted">
          <strong className="text-text">Astuce :</strong> Les identifiants sont validés en temps
          réel. Assure-toi qu'ils correspondent bien au format attendu.
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="ghost" size="md" onClick={onBack} className="flex-1">
          <ChevronLeft className="w-4 h-4 mr-2" />
          Retour
        </Button>
        <Button
          variant="primary"
          size="md"
          onClick={onContinue}
          disabled={!allValid || validating}
          className="flex-1"
        >
          {validating ? 'Validation...' : 'Tester la connexion'}
        </Button>
      </div>
    </motion.div>
  );
}
