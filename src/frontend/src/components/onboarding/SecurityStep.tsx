import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  AlertTriangle,
  Cloud,
  Terminal,
  FolderOpen,
  Mic,
  Globe,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { grantCloudConsent } from '../../lib/consent';
import type { LLMProvider } from '../../services/api';
import { libelleDuFournisseur } from '../../lib/libellesFournisseurs';
import { TEXTES_ONBOARDING } from './textes';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte } from '../ui/Carte';

interface SecurityStepProps {
  provider: LLMProvider | null;
  onNext: () => void;
  onBack: () => void;
}

interface RiskItem {
  icon: React.ElementType;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
}

// Lot C (0.48) : les textes vivent au registre (textes.ts), les icônes ici.
const ICONES_RISQUES = {
  cloud: Cloud,
  connecteurs: Terminal,
  fichiers: FolderOpen,
  web: Globe,
  voix: Mic,
} as const;

const RISKS: RiskItem[] = TEXTES_ONBOARDING.risques.map((risque) => ({
  icon: ICONES_RISQUES[risque.id],
  title: risque.title,
  description: risque.description,
  severity: risque.severity,
}));



const severityColors = {
  high: 'text-error bg-[var(--color-error-tint)] border-error/40',
  medium: 'text-warning bg-[var(--color-warning-tint)] border-warning/40',
  low: 'text-info bg-[var(--color-info-tint)] border-info/40',
};

const severityLabels = {
  high: 'Risque élevé',
  medium: 'Risque modéré',
  low: 'Risque faible',
};


export function SecurityStep({ provider, onNext, onBack }: SecurityStepProps) {
  const [acknowledged, setAcknowledged] = useState(false);
  // B-541 : la case suit le fournisseur affiché. Revenir en arrière changer de
  // fournisseur repart d'une case vide, sinon l'accord pouvait être enregistré
  // pour un fournisseur avec une case cochée pour un autre.
  useEffect(() => {
    setAcknowledged(false);
  }, [provider]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const cloudEnabled = provider !== null && provider !== 'ollama';
  // #294 : la table partagée couvre tous les fournisseurs (glm, kimi, qwen, minimax compris).
  const providerLabel = provider ? libelleDuFournisseur(provider) : null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      {/* Header avec warning */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-md bg-[var(--color-warning-tint)] border border-warning/40">
          <Shield className="w-8 h-8 text-warning" />
        </div>
        <h2 className="text-2xl font-bold text-text">Sécurité et confidentialité</h2>
        <p className="text-text-muted max-w-md mx-auto">
          THÉRÈSE est un outil puissant qui se connecte à plusieurs services.
          Comprends les risques avant de continuer.
        </p>
      </div>

      {/* Alert banner */}
      <Alerte
        ton="attention"
        titre="Important"
        icone={<AlertTriangle className="h-5 w-5 text-warning" />}
      >
        Les agents IA peuvent exécuter des commandes et agir via les tools que tu actives. Commence avec le minimum de permissions nécessaires.
      </Alerte>

      {/* Risks list */}
      <div className="space-y-2 max-h-[280px] overflow-y-auto px-2">
        {RISKS.map((risk, index) => {
          const Icon = risk.icon;
          const isExpanded = expanded === index;

          return (
            <motion.button
              key={index}
              onClick={() => setExpanded(isExpanded ? null : index)}
              aria-expanded={isExpanded}
              aria-controls={`security-detail-${index}`}
              className={cn(
                'min-h-9 w-full rounded-md border p-3 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                'hover:bg-surface-2',
                isExpanded ? 'bg-surface-2' : 'bg-transparent',
                'border-border'
              )}
              initial={false}
              animate={{ height: isExpanded ? 'auto' : 'auto' }}
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  'w-10 h-10 rounded-md flex items-center justify-center',
                  severityColors[risk.severity]
                )}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-text">{risk.title}</span>
                    <span className={cn(
                      'rounded-sm px-2 py-0.5 text-sm',
                      severityColors[risk.severity]
                    )}>
                      {severityLabels[risk.severity]}
                    </span>
                  </div>
                  {isExpanded && (
                    <motion.p
                      id={`security-detail-${index}`}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="text-sm text-text-muted mt-2"
                    >
                      {risk.description}
                    </motion.p>
                  )}
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Best practices link */}
      <a
        href="https://synoptia.fr/therese/securite"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 text-sm text-accent-cyan-ink hover:underline transition-colors"
      >
        <span>En savoir plus sur la sécurité</span>
        <ExternalLink className="w-4 h-4" />
      </a>

      {/* Consentement RGPD uniquement lorsqu'un fournisseur cloud est activé. */}
      {cloudEnabled ? <label className="flex items-start gap-3 p-4 rounded-md bg-surface border border-border cursor-pointer hover:bg-surface-elevated transition-colors">
        <input
          type="checkbox"
          id="security-consent"
          checked={acknowledged}
          onChange={(e) => setAcknowledged(e.target.checked)}
          className="mt-1 w-5 h-5 rounded-sm border-border bg-transparent text-accent-cyan-ink focus:ring-2 focus:ring-ring focus:ring-offset-0"
        />
        <div className="text-sm">
          <p className="text-text font-medium">
            Je consens au transfert de mes données vers {providerLabel}
          </p>
          <p className="text-text-muted mt-1">
            J'accepte que mes messages et le contexte utile soient envoyés à {providerLabel}{' '}
            pour traitement. Je comprends les risques et m'engage à ne pas partager de données sensibles
            (mots de passe, données clients, informations confidentielles).
          </p>
        </div>
      </label> : (
        <Carte className="flex items-start gap-3 p-4" data-testid="local-security-notice">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-accent-cyan-ink" />
          <div className="text-sm"><p className="font-medium text-text">Parcours local sans consentement cloud</p><p className="mt-1 text-text-muted">{provider === 'ollama' ? 'Ollama traite les messages sur cette machine.' : 'Aucun fournisseur cloud n’est activé pour le moment.'} Un accord distinct sera demandé au premier usage cloud réel, avec le fournisseur et les données transmis.</p></div>
        </Carte>
      )}

      {/* Navigation */}
      <div className="flex flex-wrap gap-3 pt-2">
        <Button
          variant="secondary"
          onClick={onBack}
          data-testid="onboarding-prev-btn"
          className="flex-1"
        >
          Retour
        </Button>
        <Button
          variant="primary"
          onClick={() => {
            if (cloudEnabled && provider) {
              // B-016 : la finalité 'llm' ne couvre pas les documents
              // (consent.ts : « envoyer le contenu d'un document au fournisseur
              // est une finalité DISTINCTE d'une conversation »). Le composeur
              // demande son propre accord sous 'documents' à la première pièce
              // jointe ; l'annoncer ici serait enregistrer un accord que la clé
              // écrite ne porte pas.
              grantCloudConsent('llm', provider, ['messages', 'contexte utile']);
            }
            onNext();
          }}
          disabled={cloudEnabled && !acknowledged}
          data-testid="onboarding-next-btn"
          className="flex-1"
        >
          <CheckCircle2 className="w-5 h-5" />
          <span>J'ai compris, continuer</span>
        </Button>
      </div>
    </motion.div>
  );
}
