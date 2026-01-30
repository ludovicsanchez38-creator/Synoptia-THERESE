/**
 * THÉRÈSE v2 - Email Setup Wizard
 *
 * Wizard guidé en 4 étapes pour configurer l'email.
 * Phase 1.2 - Amélioration UX
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

import { ChoiceStep } from './ChoiceStep';
import { GuideStep } from './GuideStep';
import { CredentialsStep } from './CredentialsStep';
import { VerifyStep } from './VerifyStep';
import * as api from '../../../services/api';

interface EmailSetupWizardProps {
  onComplete: () => void;
  onCancel: () => void;
}

export type EmailProvider = 'gmail' | 'smtp';

export interface WizardState {
  provider: EmailProvider | null;
  hasProject: boolean | null;
  clientId: string;
  clientSecret: string;
  useMcpCredentials: boolean;
}

export function EmailSetupWizard({ onComplete, onCancel }: EmailSetupWizardProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [wizardState, setWizardState] = useState<WizardState>({
    provider: null,
    hasProject: null,
    clientId: '',
    clientSecret: '',
    useMcpCredentials: false,
  });
  const [mcpCredentials, setMcpCredentials] = useState<api.GoogleCredentials | null>(null);

  // Load MCP credentials on mount
  useEffect(() => {
    loadSetupStatus();
  }, []);

  async function loadSetupStatus() {
    try {
      const status = await api.getEmailSetupStatus();
      if (status.google_credentials) {
        setMcpCredentials(status.google_credentials);
        // Auto-fill credentials from MCP
        setWizardState((prev) => ({
          ...prev,
          clientId: status.google_credentials!.client_id,
          clientSecret: status.google_credentials!.client_secret,
          useMcpCredentials: true,
        }));
      }
    } catch (error) {
      console.error('Failed to load setup status:', error);
    }
  }

  const updateState = (updates: Partial<WizardState>) => {
    setWizardState((prev) => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    if (step < 4) setStep((step + 1) as typeof step);
  };

  const prevStep = () => {
    if (step > 1) setStep((step - 1) as typeof step);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-2xl bg-surface border border-border/50 rounded-2xl shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
          <div>
            <h2 className="text-xl font-semibold text-text">Configuration Email</h2>
            <p className="text-sm text-text-muted">Étape {step} sur 4</p>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-background/60 rounded-lg transition-colors"
            aria-label="Fermer"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-background/60">
          <motion.div
            className="h-full bg-gradient-to-r from-accent-cyan to-accent-magenta"
            initial={{ width: '0%' }}
            animate={{ width: `${(step / 4) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {/* Content */}
        <div className="p-6">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <ChoiceStep
                key="choice"
                onSelect={(provider) => {
                  updateState({ provider });
                  // Si credentials MCP existent, skip étapes 2 et 3
                  if (mcpCredentials && provider === 'gmail') {
                    setStep(4); // Aller directement à la vérification
                  } else {
                    nextStep();
                  }
                }}
                mcpCredentials={mcpCredentials}
              />
            )}
            {step === 2 && wizardState.provider === 'gmail' && !wizardState.useMcpCredentials && (
              <GuideStep
                key="guide"
                provider={wizardState.provider}
                onHasProjectChange={(hasProject) => {
                  updateState({ hasProject });
                  nextStep();
                }}
                onBack={prevStep}
              />
            )}
            {step === 3 && wizardState.provider === 'gmail' && (
              <CredentialsStep
                key="credentials"
                clientId={wizardState.clientId}
                clientSecret={wizardState.clientSecret}
                onChange={(field, value) => {
                  updateState({ [field]: value });
                }}
                onBack={prevStep}
                onContinue={() => nextStep()}
              />
            )}
            {step === 4 && wizardState.provider === 'gmail' && (
              <VerifyStep
                key="verify"
                clientId={wizardState.clientId}
                clientSecret={wizardState.clientSecret}
                onBack={prevStep}
                onSuccess={onComplete}
              />
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
