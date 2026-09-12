/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 1
 *
 * Choix du type de connexion (Gmail OAuth vs SMTP).
 */

import { motion } from 'framer-motion';
import { Mail, Server, ShieldCheck, Zap } from 'lucide-react';
import type { EmailProvider } from './EmailSetupWizard';
import type { GoogleCredentials } from '../../../services/api';
import { Carte } from '../../ui/Carte';

interface ChoiceStepProps {
  onSelect: (provider: EmailProvider) => void;
  mcpCredentials: GoogleCredentials | null;
}

export function ChoiceStep({ onSelect, mcpCredentials }: ChoiceStepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      <div className="text-center space-y-2">
        <h3 className="text-lg font-semibold text-text">
          Comment veux-tu connecter ton email ?
        </h3>
        <p className="text-sm text-text-muted">
          {mcpCredentials
            ? '✨ Super ! J\'ai trouvé tes credentials Google MCP'
            : 'Choisis la méthode qui te convient le mieux'}
        </p>
      </div>

      {mcpCredentials && (
        <Carte as="section" className="p-4">
          <div className="flex items-start gap-3">
            <Zap className="w-5 h-5 text-accent-cyan-ink shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-text">Credentials Google détectés</p>
              <p className="text-xs text-text-muted">
                Tes identifiants OAuth du serveur MCP Google Workspace seront réutilisés.
                Tu seras redirigé directement vers la connexion !
              </p>
            </div>
          </div>
        </Carte>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Gmail OAuth */}
        <motion.button
          onClick={() => onSelect('gmail')}
          className="relative min-h-9 rounded-md border border-border bg-surface p-6 text-left text-sm transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {/* US-012 : « Recommandé » retiré - ce chemin exige de créer un
              projet Google Cloud, ce qui était l'impasse n°1 des testeurs */}
          <div className="absolute top-3 right-3">
            <span className="rounded-sm bg-surface px-2 py-1 text-sm font-medium text-text-muted">
              Avancé
            </span>
          </div>

          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-accent-tint">
            <Mail className="w-6 h-6 text-accent-cyan-ink" />
          </div>

          <h4 className="text-base font-semibold text-text mb-2">Gmail OAuth</h4>
          <p className="text-sm text-text-muted mb-4">
            Connexion sécurisée via Google OAuth 2.0
          </p>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-success" />
              <span>Très sécurisé (OAuth PKCE)</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-success" />
              <span>Officiel Google</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-success" />
              <span>Révocable à tout moment</span>
            </div>
          </div>
        </motion.button>

        {/* SMTP Classique */}
        <motion.button
          onClick={() => onSelect('smtp')}
          className="relative min-h-9 rounded-md border border-border bg-surface p-6 text-left text-sm transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <div className="absolute top-3 right-3">
            <span className="rounded-sm bg-accent-tint px-2 py-1 text-sm font-medium text-accent-cyan-ink">
              Recommandé
            </span>
          </div>

          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-2">
            <Server className="w-6 h-6 text-text-muted" />
          </div>

          <h4 className="text-base font-semibold text-text mb-2">SMTP / IMAP classique</h4>
          <p className="text-sm text-text-muted mb-4">
            Gmail (mot de passe d'application), OVH, Gandi, Infomaniak...
          </p>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-success" />
              <span>Prêt en 2 minutes, sans projet Google Cloud</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-success" />
              <span>Compatible tous providers</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-success" />
              <span>Mot de passe chiffré localement</span>
            </div>
          </div>
        </motion.button>
      </div>

      {/* US-012 : le chemin Gmail SANS créer de projet Google Cloud doit être
          visible - c'était l'impasse n°1 des testeurs alpha */}
      <Carte as="section" className="p-4">
        <p className="text-sm text-text-muted">
          <strong className="text-text">Gmail sans prise de tête :</strong> choisis « SMTP / IMAP
          classique », sélectionne le preset Gmail et utilise un{' '}
          <strong className="text-text">mot de passe d'application</strong> (Google →
          myaccount.google.com/apppasswords, validation en 2 étapes requise). Aucune
          configuration Google Cloud n'est nécessaire. L'option Gmail OAuth reste là pour
          ceux qui préfèrent un accès API complet (elle demande de créer ses propres
          identifiants OAuth dans Google Cloud Console).
        </p>
      </Carte>
    </motion.div>
  );
}
