/**
 * THERESE v2 - Working Directory Step
 *
 * Fourth step of the onboarding wizard - Select default working directory.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FolderOpen, Check, AlertCircle } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import * as api from '../../services/api';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';

interface WorkingDirStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function WorkingDirStep({ onNext, onBack }: WorkingDirStepProps) {
  const [workingDir, setWorkingDir] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial state
  useEffect(() => {
    async function loadState() {
      try {
        const workingDirData = await api.getWorkingDirectory().catch(() => ({ path: null, exists: false }));
        setWorkingDir(workingDirData?.path || null);
      } catch (err) {
        console.error('Failed to load working directory:', err);
      } finally {
        setLoading(false);
      }
    }
    loadState();
  }, []);

  async function handleSelectDir() {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
      });

      if (selected && typeof selected === 'string') {
        setSaving(true);
        setError(null);
        const result = await api.setWorkingDirectory(selected);
        setWorkingDir(result.path);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sélection');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner taille="zone" className="text-accent-cyan-ink" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col px-8 py-6 h-full"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-md bg-accent-cyan/10 flex items-center justify-center">
          <FolderOpen className="w-5 h-5 text-accent-cyan-ink" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-text">Dossier de travail</h2>
          <p className="text-sm text-text-muted">Où se trouvent tes fichiers de travail ?</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="w-full max-w-md"
        >
          {/* Icon */}
          <div className="w-20 h-20 rounded-md bg-accent-cyan/10 flex items-center justify-center mb-6 mx-auto border border-border/30">
            <FolderOpen className="w-10 h-10 text-accent-cyan-ink" />
          </div>

          {/* Description */}
          <p className="text-text-muted mb-6">
            {/* BUG-167. Le texte promettait « la recherche de fichiers et
                l'organisation de tes documents ». En réalité, ce dossier est
                le point de départ de l'explorateur : rien n'est parcouru,
                indexé ni rendu consultable dans le chat tant que tu ne l'as pas
                demandé. Le testeur l'a relevé d'un mot — « ben j'aimerais bien
                voir ça ! ». Promettre ce qu'on ne fait pas coûte plus cher que
                de faire moins. */}
            L'explorateur de fichiers s'ouvrira sur ce dossier. Tu pourras y choisir
            les documents à confier à THÉRÈSE, un par un.
          </p>

          {/* Current directory display */}
          {workingDir ? (
            <div className="mb-6">
              <div className="flex items-center gap-2 px-4 py-3 bg-[var(--color-success-tint)] border border-success/40 rounded-md">
                <Check className="w-4 h-4 text-success" />
                <span className="text-sm text-success">Dossier configuré</span>
              </div>
              <div className="mt-2 p-3 bg-background/40 rounded-md border border-border/30">
                <p className="text-xs text-text font-mono truncate" title={workingDir}>
                  {workingDir}
                </p>
              </div>
            </div>
          ) : (
            <div className="mb-6 px-4 py-3 bg-[var(--color-warning-tint)] border border-warning/40 rounded-md">
              <div className="flex items-center gap-2 justify-center">
                <AlertCircle className="w-4 h-4 text-warning" />
                <span className="text-sm text-warning">Aucun dossier configuré</span>
              </div>
            </div>
          )}

          {/* Select button */}
          <Button
            variant={workingDir ? 'ghost' : 'primary'}
            onClick={handleSelectDir}
            disabled={saving}
            className="w-full"
          >
            {saving ? (
              <>
                <Spinner taille="bouton" className="mr-2" />
                Sélection...
              </>
            ) : (
              <>
                <FolderOpen className="w-4 h-4 mr-2" />
                {workingDir ? 'Changer de dossier' : 'Sélectionner un dossier'}
              </>
            )}
          </Button>

          {/* Error */}
          {error && (
            <div className="mt-4 flex items-center gap-2 px-3 py-2 bg-[var(--color-error-tint)] border border-error/40 rounded-md">
              <AlertCircle className="w-4 h-4 text-error" />
              <span className="text-sm text-error">{error}</span>
            </div>
          )}
        </motion.div>
      </div>

      {/* Footer */}
      <div className="flex justify-between pt-4 border-t border-border/30">
        <Button variant="ghost" onClick={onBack} data-testid="onboarding-prev-btn">
          Retour
        </Button>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={onNext} data-testid="onboarding-skip-btn">
            Passer
          </Button>
          <Button
            variant="primary"
            onClick={onNext}
            disabled={!workingDir}
            title={!workingDir ? 'Sélectionne un dossier ou clique sur "Passer"' : undefined}
            data-testid="onboarding-next-btn"
          >
            Continuer
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
