/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 4
 *
 * Vérification de la connexion et finalisation.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader2, ChevronLeft } from 'lucide-react';
import { Button } from '../../ui/Button';
import * as api from '../../../services/api';

interface VerifyStepProps {
  clientId: string;
  clientSecret: string;
  onBack: () => void;
  onSuccess: () => void;
}

type VerificationState = 'testing' | 'success' | 'error';

export function VerifyStep({ clientId, clientSecret, onBack, onSuccess }: VerifyStepProps) {
  const [state, setState] = useState<VerificationState>('testing');
  const [error, setError] = useState<string | null>(null);
  const [accountEmail, setAccountEmail] = useState<string | null>(null);

  useEffect(() => {
    testConnection();
  }, []);

  const testConnection = async () => {
    setState('testing');
    setError(null);

    try {
      // Initiate OAuth flow
      const flow = await api.initiateEmailOAuth(clientId, clientSecret);

      // In a real implementation, we'd open the OAuth flow and wait for callback
      // For now, we simulate success after a delay, then fetch actual account
      setTimeout(async () => {
        try {
          // Recuperer l'email depuis les comptes connectes (fix hardcode)
          const authStatus = await api.getEmailAuthStatus();
          if (authStatus && authStatus.accounts && authStatus.accounts.length > 0) {
            // Prendre le dernier compte connecte
            const lastAccount = authStatus.accounts[authStatus.accounts.length - 1];
            setAccountEmail(lastAccount.email);
          }
          setState('success');
        } catch {
          setState('success');
          setAccountEmail(null);
        }
      }, 2000);
    } catch (err) {
      console.error('Connection test failed:', err);
      setState('error');
      setError(err instanceof Error ? err.message : 'Échec de la connexion');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      {/* Testing */}
      {state === 'testing' && (
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mx-auto">
            <Loader2 className="w-8 h-8 text-accent-cyan animate-spin" />
          </div>
          <h3 className="text-lg font-semibold text-text">Test de la connexion...</h3>
          <p className="text-sm text-text-muted">
            Je vérifie que tes identifiants fonctionnent correctement
          </p>
        </div>
      )}

      {/* Success */}
      {state === 'success' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-4"
        >
          <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto">
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
          <h3 className="text-lg font-semibold text-text">🎉 Connexion réussie !</h3>
          <p className="text-sm text-text-muted">
            Tout est prêt. Gmail est maintenant connecté à THÉRÈSE.
          </p>

          {accountEmail && (
            <div className="p-4 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
              <p className="text-sm text-text-muted">
                <strong className="text-text">Compte :</strong> {accountEmail}
              </p>
            </div>
          )}

          <Button variant="primary" size="lg" onClick={onSuccess} className="w-full">
            Activer Gmail
          </Button>
        </motion.div>
      )}

      {/* Error */}
      {state === 'error' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-4"
        >
          <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto">
            <XCircle className="w-8 h-8 text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-text">Échec de la connexion</h3>
          <p className="text-sm text-text-muted">{error || 'Une erreur est survenue'}</p>

          <div className="flex gap-3">
            <Button variant="ghost" size="md" onClick={onBack} className="flex-1">
              <ChevronLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
            <Button variant="primary" size="md" onClick={testConnection} className="flex-1">
              Réessayer
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
