/**
 * THERESE v2 - Complete Step
 *
 * Final step of the onboarding wizard - Celebration and recap.
 */

import { useCallback, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { PartyPopper, Check, User, Cpu, FolderOpen, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import * as api from '../../services/api';
import { Button } from '../ui/Button';

interface CompleteStepProps {
  onComplete: () => void;
  onBack: () => void;
}

interface SetupSummary {
  profile: api.UserProfile | null;
  llmConfig: api.LLMConfig | null;
  workingDir: string | null;
}

export function CompleteStep({ onComplete, onBack }: CompleteStepProps) {
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
      llmResult.status === 'rejected' ? 'LLM' : null,
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
      title: 'LLM',
      value: summary.llmConfig?.available
        ? `${summary.llmConfig.provider} / ${summary.llmConfig.model.split('-').slice(0, 2).join('-')}`
        : 'À configurer',
      configured: !!summary.llmConfig?.available,
      unavailable: summaryUnavailable.includes('LLM'),
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
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
        className="mb-8"
      >
        <div className="w-24 h-24 rounded-2xl bg-accent-cyan/10 flex items-center justify-center border border-border/30">
          <PartyPopper className="w-12 h-12 text-accent-cyan" />
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
          <div role="status" className="rounded-xl border border-info/40 bg-[var(--color-info-tint)] p-4 text-sm text-info">
            Vérification de la configuration…
          </div>
        )}
        {!loading && summaryUnavailable.length > 0 && (
          <div role="alert" className="rounded-xl border border-warning/40 bg-[var(--color-warning-tint)] p-4 text-left text-sm text-warning">
            <p><strong>Récapitulatif partiel.</strong> Indisponible{summaryUnavailable.length > 1 ? 's' : ''} : {summaryUnavailable.join(', ')}.</p>
            <button type="button" onClick={() => void loadSummary()} className="mt-2 rounded-md border border-warning px-3 py-2 font-semibold">Réessayer</button>
          </div>
        )}
        {!loading && summaryItems.map((item, index) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 + index * 0.1 }}
            className="flex items-center gap-3 p-4 rounded-xl bg-background/40 border border-border/30 text-left"
          >
            <div
              className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
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
          </motion.div>
        ))}
      </motion.div>

      {/* Tips */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.9 }}
        className="mb-6 p-3 rounded-xl bg-accent-cyan/5 border border-accent-cyan/20 text-left w-full max-w-md"
      >
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-accent-cyan" />
          <span className="text-sm font-medium text-accent-cyan">Astuce</span>
        </div>
        <p className="text-xs text-text-muted">
          Tu peux à tout moment modifier ces paramètres dans les Paramètres (raccourci {settingsShortcut}+,).
        </p>
      </motion.div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 rounded-xl bg-[var(--color-error-tint)] border border-error/40 text-left w-full max-w-md"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-error shrink-0" />
            <span className="text-sm text-error flex-1">{error}</span>
            <button
              onClick={handleRetry}
              className="flex items-center gap-1 text-xs text-error hover:text-error transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Réessayer
            </button>
          </div>
        </motion.div>
      )}

      </div>

      {/* Footer épinglé - toujours visible */}
      <div className="flex justify-between w-full pt-4 mt-4 border-t border-border/30 shrink-0">
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
