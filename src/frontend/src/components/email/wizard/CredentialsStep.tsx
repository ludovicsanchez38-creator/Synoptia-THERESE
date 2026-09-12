/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 3
 *
 * Saisie des identifiants avec validation temps réel.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Key, ChevronLeft, Upload } from 'lucide-react';
import { Button } from '../../ui/Button';
import * as api from '../../../services/api';
import { Alerte } from '../../ui/Alerte';
import { Carte } from '../../ui/Carte';
import { FormField } from '../../ui/FormField';
import { Input } from '../../ui/Input';

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
  // B-529 : un échec réseau de la vérification se voit, distinct d'une saisie absente.
  const [validationError, setValidationError] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
        onChange('clientId', creds.client_id);
        onChange('clientSecret', creds.client_secret);
        setImportError(null);
      } catch {
        setImportError('Fichier JSON invalide');
      }
    };
    reader.readAsText(file);
    // Reset pour permettre de re-sélectionner le même fichier
    e.target.value = '';
  }, [onChange]);

  // Validation temps réel (debounced)
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (clientId.trim() && clientSecret.trim()) {
        setValidating(true);
        setValidationError(null);
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
          setValidationError('La vérification des identifiants n’a pas abouti : le serveur n’a pas répondu. Modifie un champ pour réessayer.');
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
        <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-accent-tint">
          <Key className="w-6 h-6 text-accent-cyan-ink" />
        </div>
        <h3 className="text-lg font-semibold text-text">Entre tes identifiants</h3>
        <p className="text-sm text-text-muted">
          Copie l'ID client et le Code secret du client depuis Google Cloud Console
        </p>
      </div>

      {/* ID client */}
      <FormField
        label="ID client"
        htmlFor="clientId"
        description={validation.clientId?.valid ? validation.clientId.message : undefined}
        error={validation.clientId && !validation.clientId.valid ? validation.clientId.message : undefined}
      >
          <Input
            id="clientId"
            type="text"
            value={clientId}
            onChange={(e) => onChange('clientId', e.target.value)}
            placeholder="123456789-abc...apps.googleusercontent.com"
            error={validation.clientId?.valid === false}
          />
      </FormField>

      {/* Code secret du client */}
      <FormField
        label="Code secret du client"
        htmlFor="clientSecret"
        description={validation.clientSecret?.valid ? validation.clientSecret.message : undefined}
        error={validation.clientSecret && !validation.clientSecret.valid ? validation.clientSecret.message : undefined}
      >
          <Input
            id="clientSecret"
            type="password"
            value={clientSecret}
            onChange={(e) => onChange('clientSecret', e.target.value)}
            placeholder="GOCSPX-..."
            error={validation.clientSecret?.valid === false}
          />
      </FormField>
      {validationError && <Alerte>{validationError}</Alerte>}

      {/* Import credentials.json + Info */}
      <Carte as="section" className="space-y-3 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-text-muted">
            <strong className="text-text">Astuce :</strong> Tu peux importer directement le fichier <code className="text-accent-cyan-ink">credentials.json</code> téléchargé depuis Google Cloud Console.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleImportCredentials}
            className="hidden"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            className="shrink-0 ml-3"
          >
            <Upload className="w-4 h-4 mr-1.5" />
            Importer
          </Button>
        </div>
        {importError && (
          <Alerte>{importError}</Alerte>
        )}
      </Carte>

      {/* Actions */}
      <div className="flex flex-wrap gap-3 max-[840px]:items-stretch">
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
