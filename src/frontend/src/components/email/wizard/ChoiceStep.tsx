/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 1
 *
 * Choix du type de connexion (Gmail OAuth vs SMTP).
 */

import { motion } from 'framer-motion';
import { Mail, Server, ShieldCheck, AlertCircle, Zap } from 'lucide-react';
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
          <div className="absolute top-3 right-3">
            <span className="px-2 py-1 text-xs font-medium bg-accent-cyan/20 text-accent-cyan rounded-full">
              Recommandé
            </span>
          </div>

          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
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
          className="relative p-6 bg-background/40 border-2 border-border/30 rounded-xl hover:border-border/60 transition-all group text-left"
        >
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-text-muted/20 to-text-muted/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Server className="w-6 h-6 text-text-muted" />
          </div>

          <h4 className="text-base font-semibold text-text mb-2">SMTP Classique</h4>
          <p className="text-sm text-text-muted mb-4">
            Connexion SMTP/IMAP (OVH, Gandi, etc.)
          </p>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Configuration simple</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>Compatible tous providers</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-yellow-400">
              <AlertCircle className="w-4 h-4" />
              <span>Mot de passe en clair</span>
            </div>
          </div>
        </motion.button>
      </div>

      <div className="p-4 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
        <p className="text-sm text-text-muted">
          <strong className="text-text">Note :</strong> Gmail OAuth est recommandé pour une sécurité maximale.
          Le SMTP classique sera disponible prochainement (Phase 1.1).
        </p>
      </div>
    </motion.div>
  );
}
