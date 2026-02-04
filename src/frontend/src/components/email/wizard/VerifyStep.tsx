/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 4
 *
 * Autorisation OAuth via navigateur et vérification de la connexion.
 */

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader2, ChevronLeft, ExternalLink } from 'lucide-react';
import { open } from '@tauri-apps/plugin-shell';
import { Button } from '../../ui/Button';
import * as api from '../../../services/api';

interface VerifyStepProps {
  clientId: string;
  clientSecret: string;
  onBack: () => void;
  onSuccess: () => void;
}

type VerificationState = 'initiating' | 'waiting' | 'success' | 'error';

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

export function VerifyStep({ clientId, clientSecret, onBack, onSuccess }: VerifyStepProps) {
  const [state, setState] = useState<VerificationState>('initiating');
  const [error, setError] = useState<string | null>(null);
  const [accountEmail, setAccountEmail] = useState<string | null>(null);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const initialAccountCountRef = useRef<number>(0);

  useEffect(() => {
    startOAuthFlow();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  async function startOAuthFlow() {
    setState('initiating');
    setError(null);
    setAuthUrl(null);

    try {
      // Mémoriser le nombre de comptes existants avant l'autorisation
      const currentStatus = await api.getEmailAuthStatus();
      initialAccountCountRef.current = currentStatus.accounts?.length || 0;

      // Initier le flow OAuth
      const flow = await api.initiateEmailOAuth(clientId, clientSecret);
      setAuthUrl(flow.auth_url);

      // Ouvrir le navigateur par défaut
      try {
        await open(flow.auth_url);
      } catch {
        // Fallback si Tauri shell n'est pas disponible
        window.open(flow.auth_url, '_blank');
      }

      setState('waiting');

      // Poller le status toutes les 3 secondes
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.getEmailAuthStatus();
          const newAccountCount = status.accounts?.length || 0;

          // Un nouveau compte a été ajouté
          if (newAccountCount > initialAccountCountRef.current) {
            if (pollRef.current) clearInterval(pollRef.current);
            if (timeoutRef.current) clearTimeout(timeoutRef.current);

            const newAccount = status.accounts[status.accounts.length - 1];
            setAccountEmail(newAccount.email);
            setState('success');
          }
        } catch (err) {
          // Ignorer les erreurs de polling (réseau temporaire, etc.)
          console.warn('Polling auth status failed:', err);
        }
      }, POLL_INTERVAL_MS);

      // Timeout après 5 minutes
      timeoutRef.current = setTimeout(() => {
        if (pollRef.current) clearInterval(pollRef.current);
        setState('error');
        setError('Délai d\'attente dépassé. L\'autorisation n\'a pas abouti dans les 5 minutes.');
      }, POLL_TIMEOUT_MS);

    } catch (err) {
      console.error('OAuth flow initiation failed:', err);
      setState('error');
      setError(err instanceof Error ? err.message : 'Échec de l\'initiation OAuth');
    }
  }

  async function openAuthUrlManually() {
    if (!authUrl) return;
    try {
      await open(authUrl);
    } catch {
      window.open(authUrl, '_blank');
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      {/* Initiating */}
      {state === 'initiating' && (
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mx-auto">
            <Loader2 className="w-8 h-8 text-accent-cyan animate-spin" />
          </div>
          <h3 className="text-lg font-semibold text-text">Préparation de l'autorisation...</h3>
          <p className="text-sm text-text-muted">
            Ouverture de Google dans ton navigateur
          </p>
        </div>
      )}

      {/* Waiting for authorization */}
      {state === 'waiting' && (
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mx-auto">
            <Loader2 className="w-8 h-8 text-accent-cyan animate-spin" />
          </div>
          <h3 className="text-lg font-semibold text-text">En attente d'autorisation...</h3>
          <p className="text-sm text-text-muted">
            Autorise THÉRÈSE dans la fenêtre Google qui s'est ouverte dans ton navigateur.
          </p>
          <p className="text-xs text-text-muted/70">
            Une fois l'autorisation accordée, cette page se mettra à jour automatiquement.
          </p>

          {authUrl && (
            <button
              onClick={openAuthUrlManually}
              className="inline-flex items-center gap-2 text-xs text-accent-cyan hover:text-accent-cyan/80 transition-colors mt-2"
            >
              <ExternalLink className="w-3 h-3" />
              Rouvrir la page d'autorisation Google
            </button>
          )}

          <div className="pt-2">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ChevronLeft className="w-4 h-4 mr-2" />
              Annuler
            </Button>
          </div>
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
          <h3 className="text-lg font-semibold text-text">Connexion réussie !</h3>
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
            <Button variant="primary" size="md" onClick={startOAuthFlow} className="flex-1">
              Réessayer
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
