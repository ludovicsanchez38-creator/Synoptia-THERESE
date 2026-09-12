/**
 * THERESE v2 - Complete Step
 *
 * Final step of the onboarding wizard - Celebration and recap.
 */

import { useCallback, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { PartyPopper, Check, User, Cpu, FolderOpen, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import * as api from '../../services/api';
import { libelleDuFournisseur } from '../../lib/libellesFournisseurs';
import { Button } from '../ui/Button';
import { Alerte } from '../ui/Alerte';
import { Carte } from '../ui/Carte';

interface CompleteStepProps {
  onComplete: () => void;
  onBack: () => void;
  /** B-199 : l'étape du service d'IA a été passée (« Configurer plus tard »). */
  llmSkipped?: boolean;
  /** #162 : « plus tard » choisi, mais ce fournisseur n'a pas pu être effacé au serveur et reste actif. */
  serviceIaConserve?: string | null;
}

interface SetupSummary {
  profile: api.UserProfile | null;
  llmConfig: api.LLMConfig | null;
  workingDir: string | null;
}

export function CompleteStep({ onComplete, onBack, llmSkipped = false, serviceIaConserve = null }: CompleteStepProps) {
  const [summary, setSummary] = useState<SetupSummary>({
    profile: null,
    llmConfig: null,
    workingDir: null,
  });
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryUnavailable, setSummaryUnavailable] = useState<string[]>([]);

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setSummaryUnavailable([]);
    const [profileResult, llmResult, workingDirResult] = await Promise.allSettled([
      api.getProfile(),
      api.getLLMConfig(),
      api.getWorkingDirectory(),
    ]);
    setSummary({
      profile: profileResult.status === 'fulfilled' ? profileResult.value : null,
      llmConfig: llmResult.status === 'fulfilled' ? llmResult.value : null,
      workingDir: workingDirResult.status === 'fulfilled' ? workingDirResult.value?.path || null : null,
    });
    setSummaryUnavailable([
      profileResult.status === 'rejected' ? 'Profil' : null,
      llmResult.status === 'rejected' ? 'Service d’IA' : null,
      workingDirResult.status === 'rejected' ? 'Dossier de travail' : null,
    ].filter((label): label is string => Boolean(label)));
    setLoading(false);
  }, []);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  async function handleComplete() {
    setCompleting(true);
    setError(null);
    try {
      await api.completeOnboarding();
      window.dispatchEvent(new Event('therese:llm-config-changed'));
      onComplete();
    } catch (err) {
      console.error('Failed to complete onboarding:', err);
      setError(err instanceof Error ? err.message : 'Erreur lors de la finalisation');
      setCompleting(false);
    }
  }

  const summaryItems = [
    {
      icon: User,
      title: 'Profil',
      value: summary.profile?.display_name || 'Non configuré',
      configured: !!summary.profile?.name,
      unavailable: summaryUnavailable.includes('Profil'),
    },
    {
      icon: Cpu,
      // « Configuré » doit refléter la disponibilité RÉELLE (clé cloud présente
      // ou Ollama opérationnel), pas la simple existence d'un provider par
      // défaut : sinon « Configurer plus tard » affichait quand même une coche
      // verte et openai/gpt-5.5 (faux succès, finding Codex 16/07).
      title: 'Service d’IA',
      // B-199 : « Configurer plus tard » l'emporte sur la configuration par
      // défaut relue au serveur - le récapitulatif dit ce que la personne a
      // choisi dans l'assistant, pas ce que le serveur porte en réglage initial.
      value: llmSkipped
        ? serviceIaConserve
          ? `À configurer plus tard (le réglage ${libelleDuFournisseur(serviceIaConserve)} n’a pas pu être effacé et reste actif)`
          : 'À configurer plus tard'
        : summary.llmConfig?.available
        // B-243 : le modèle s'écrit en entier. La troncature aux deux premiers
        // segments fabriquait un identifiant absent de toute liste
        // (mistral-medium-latest -> « mistral-medium », claude-opus-4-8 ->
        // « claude-opus »). Le débordement est déjà tenu par `truncate` et le
        // `title` de la ligne, qui rendent la valeur entière au survol.
        ? `${summary.llmConfig.provider} / ${summary.llmConfig.model}`
        : 'À configurer',
      configured: !llmSkipped && !!summary.llmConfig?.available,
      unavailable: !llmSkipped && summaryUnavailable.includes('Service d’IA'),
    },
    {
      icon: FolderOpen,
      title: 'Dossier de travail',
      value: summary.workingDir
        ? summary.workingDir.split('/').slice(-2).join('/')
        : 'Non configuré',
      configured: !!summary.workingDir,
      unavailable: summaryUnavailable.includes('Dossier de travail'),
    },
  ];

  // Retry function
  function handleRetry() {
    setError(null);
    handleComplete();
  }

  const settingsShortcut = /Mac|iPhone|iPad/.test(navigator.platform) ? 'Cmd' : 'Ctrl';

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col px-8 py-6 h-full"
    >
      {/* Zone scrollable : le pied de page reste épinglé, jamais coupé hors de
          la fenêtre même à 1280×900 (finding Codex 16/07). */}
      <div className="flex flex-1 flex-col items-center text-center overflow-y-auto min-h-0 w-full">
      {/* Celebration Animation */}
      <motion.div
        initial={{ opacity: 0, rotate: -180 }}
        animate={{ opacity: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
        className="mb-8"
      >
        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-accent-tint">
          <PartyPopper className="h-12 w-12 text-accent" />
        </div>
      </motion.div>

      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-text mb-3">
          C'est parti !
        </h1>
        <p className="text-text-muted text-lg max-w-md">
          THÉRÈSE est prête à t'accompagner. Voici un résumé de ta configuration.
        </p>
      </motion.div>

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="w-full max-w-md space-y-3 mb-6"
      >
        {loading && (
          <div role="status" className="rounded-md border border-info/40 bg-[var(--color-info-tint)] p-4 text-sm text-info">
            Vérification de la configuration…
          </div>
        )}
        {!loading && summaryUnavailable.length > 0 && (
          <Alerte
            ton="attention"
            titre="Récapitulatif partiel"
            className="text-left"
            action={<Button variant="secondary" size="sm" onClick={() => void loadSummary()}>Réessayer</Button>}
          >Indisponible{summaryUnavailable.length > 1 ? 's' : ''} : {summaryUnavailable.join(', ')}.</Alerte>
        )}
        {!loading && summaryItems.map((item) => (
          <Carte
            key={item.title}
            className="flex items-center gap-3 p-4 text-left"
            data-testid={`summary-${item.title.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-')}`}
            data-configured={item.configured ? 'true' : 'false'}
          >
            <div
              className={`w-10 h-10 rounded-md flex items-center justify-center shrink-0 ${
                item.configured
                  ? 'bg-[var(--color-success-tint)] text-success'
                  : 'bg-[var(--color-warning-tint)] text-warning'
              }`}
            >
              {item.configured ? <Check className="w-5 h-5" /> : <item.icon className="w-5 h-5" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text">{item.title}</p>
              <p className="text-xs text-text-muted truncate" title={String(item.value)}>
                {item.unavailable ? 'Indisponible' : item.value}
              </p>
            </div>
          </Carte>
        ))}
      </motion.div>

      {/* Tips */}
      <Carte
        as="section"
        className="mb-6 w-full max-w-md p-3 text-left"
      >
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-accent-cyan-ink" />
          <span className="text-sm font-medium text-accent-cyan-ink">Astuce</span>
        </div>
        <p className="text-xs text-text-muted">
          Tu peux à tout moment modifier ces paramètres dans les Paramètres (raccourci {settingsShortcut}+,).
        </p>
      </Carte>

      {/* Error */}
      {error && (
        <Alerte
          className="mb-4 w-full max-w-md text-left"
          icone={<AlertCircle className="h-4 w-4 text-error" />}
          action={<Button variant="secondary" size="sm" onClick={handleRetry}><RefreshCw className="h-3 w-3" />Réessayer</Button>}
        >{error}</Alerte>
      )}

      </div>

      {/* Footer épinglé - toujours visible */}
      <div className="mt-4 flex w-full shrink-0 flex-wrap justify-between gap-3 border-t border-border pt-4">
        <Button variant="ghost" onClick={onBack} data-testid="onboarding-prev-btn">
          Retour
        </Button>
        <Button
          variant="primary"
          onClick={handleComplete}
          disabled={completing}
          className="px-8"
          data-testid="onboarding-complete-btn"
        >
          {completing ? 'Démarrage...' : 'Commencer'}
        </Button>
      </div>
    </motion.div>
  );
}
