/**
 * THERESE v2 - Complete Step
 *
 * Final step of the onboarding wizard - Celebration and recap.
 */

import { useState, useEffect } from 'react';
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

  // Load summary data
  useEffect(() => {
    async function loadSummary() {
      try {
        const [profile, llmConfig, workingDirData] = await Promise.all([
          api.getProfile().catch(() => null),
          api.getLLMConfig().catch(() => null),
          api.getWorkingDirectory().catch(() => ({ path: null, exists: false })),
        ]);
        setSummary({
          profile,
          llmConfig,
          workingDir: workingDirData?.path || null,
        });
      } catch (err) {
        console.error('Failed to load summary:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSummary();
  }, []);

  async function handleComplete() {
    setCompleting(true);
    setError(null);
    try {
      await api.completeOnboarding();
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
    },
    {
      icon: Cpu,
      title: 'LLM',
      value: summary.llmConfig
        ? `${summary.llmConfig.provider} / ${summary.llmConfig.model.split('-').slice(0, 2).join('-')}`
        : 'Non configuré',
      configured: !!summary.llmConfig,
    },
    {
      icon: FolderOpen,
      title: 'Dossier de travail',
      value: summary.workingDir
        ? summary.workingDir.split('/').slice(-2).join('/')
        : 'Non configuré',
      configured: !!summary.workingDir,
    },
  ];

  // Retry function
  function handleRetry() {
    setError(null);
    handleComplete();
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center text-center px-8 py-6 h-full overflow-y-auto"
    >
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
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-yellow-500/20 text-yellow-400'
              }`}
            >
              {item.configured ? <Check className="w-5 h-5" /> : <item.icon className="w-5 h-5" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text">{item.title}</p>
              <p className="text-xs text-text-muted truncate" title={String(item.value)}>
                {item.value}
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
          Tu peux à tout moment modifier ces paramètres dans les Paramètres (raccourci Cmd+,).
        </p>
      </motion.div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-left w-full max-w-md"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span className="text-sm text-red-400 flex-1">{error}</span>
            <button
              onClick={handleRetry}
              className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Réessayer
            </button>
          </div>
        </motion.div>
      )}

      {/* Footer */}
      <div className="flex justify-between w-full pt-4 border-t border-border/30">
        <Button variant="ghost" onClick={onBack}>
          Retour
        </Button>
        <Button
          variant="primary"
          onClick={handleComplete}
          disabled={completing}
          className="px-8"
        >
          {completing ? 'Démarrage...' : 'Commencer'}
        </Button>
      </div>
    </motion.div>
  );
}
