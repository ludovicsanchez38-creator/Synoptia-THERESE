/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 1
 *
 * Choix du type de connexion (Gmail OAuth vs SMTP).
 */

import { motion } from 'framer-motion';
import { Mail, Server, ShieldCheck, Zap } from 'lucide-react';
import type { EmailProvider } from './EmailSetupWizard';
import type { GoogleCredentials } from '../../../services/api';

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
        <div className="p-4 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
          <div className="flex items-start gap-3">
            <Zap className="w-5 h-5 text-accent-cyan shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-text">Credentials Google détectés</p>
              <p className="text-xs text-text-muted">
                Tes identifiants OAuth du serveur MCP Google Workspace seront réutilisés.
                Tu seras redirigé directement vers la connexion !
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Gmail OAuth */}
        <motion.button
          onClick={() => onSelect('gmail')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="relative p-6 bg-background/40 border-2 border-accent-cyan/30 rounded-xl hover:border-accent-cyan/60 transition-all group text-left"
        >
          {/* US-012 : « Recommandé » retiré - ce chemin exige de créer un
              projet Google Cloud, ce qui était l'impasse n°1 des testeurs */}
          <div className="absolute top-3 right-3">
            <span className="px-2 py-1 text-xs font-medium bg-surface text-text-muted rounded-[6px]">
              Avancé
            </span>
          </div>

          <div className="w-12 h-12 rounded-[8px] bg-accent-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Mail className="w-6 h-6 text-accent-cyan" />
          </div>

          <h4 className="text-base font-semibold text-text mb-2">Gmail OAuth</h4>
          <p className="text-sm text-text-muted mb-4">
            Connexion sécurisée via Google OAuth 2.0
          </p>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Très sécurisé (OAuth PKCE)</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Officiel Google</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Révocable à tout moment</span>
            </div>
          </div>
        </motion.button>

        {/* SMTP Classique */}
        <motion.button
          onClick={() => onSelect('smtp')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="relative p-6 bg-background/40 border-2 border-accent-cyan/30 rounded-xl hover:border-accent-cyan/60 transition-all group text-left"
        >
          <div className="absolute top-3 right-3">
            <span className="px-2 py-1 text-xs font-medium bg-accent-cyan/20 text-accent-cyan rounded-[6px]">
              Recommandé
            </span>
          </div>

          <div className="w-12 h-12 rounded-[8px] bg-text-muted/15 border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Server className="w-6 h-6 text-text-muted" />
          </div>

          <h4 className="text-base font-semibold text-text mb-2">SMTP / IMAP classique</h4>
          <p className="text-sm text-text-muted mb-4">
            Gmail (mot de passe d'application), OVH, Gandi, Infomaniak...
          </p>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Prêt en 2 minutes, sans projet Google Cloud</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Compatible tous providers</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Mot de passe chiffré localement</span>
            </div>
          </div>
        </motion.button>
      </div>

      {/* US-012 : le chemin Gmail SANS créer de projet Google Cloud doit être
          visible - c'était l'impasse n°1 des testeurs alpha */}
      <div className="p-4 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
        <p className="text-sm text-text-muted">
          <strong className="text-text">Gmail sans prise de tête :</strong> choisis « SMTP / IMAP
          classique », sélectionne le preset Gmail et utilise un{' '}
          <strong className="text-text">mot de passe d'application</strong> (Google →
          myaccount.google.com/apppasswords, validation en 2 étapes requise). Aucune
          configuration Google Cloud n'est nécessaire. L'option Gmail OAuth reste là pour
          ceux qui préfèrent un accès API complet (elle demande de créer ses propres
          identifiants OAuth dans Google Cloud Console).
        </p>
      </div>
    </motion.div>
  );
}
