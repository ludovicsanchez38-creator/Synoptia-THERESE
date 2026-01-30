/**
 * THERESE v2 - Working Directory Step
 *
 * Fourth step of the onboarding wizard - Select default working directory.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FolderOpen, Check, AlertCircle, Loader2 } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import * as api from '../../services/api';
import { Button } from '../ui/Button';

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
        <Loader2 className="w-8 h-8 animate-spin text-accent-cyan" />
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
        <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center">
          <FolderOpen className="w-5 h-5 text-accent-cyan" />
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
          <div className="w-20 h-20 rounded-2xl bg-accent-cyan/10 flex items-center justify-center mb-6 mx-auto border border-border/30">
            <FolderOpen className="w-10 h-10 text-accent-cyan" />
          </div>

          {/* Description */}
          <p className="text-text-muted mb-6">
            THÉRÈSE utilisera ce dossier comme point de départ pour la recherche de fichiers
            et l'organisation de tes documents.
          </p>

          {/* Current directory display */}
          {workingDir ? (
            <div className="mb-6">
              <div className="flex items-center gap-2 px-4 py-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Dossier configuré</span>
              </div>
              <div className="mt-2 p-3 bg-background/40 rounded-lg border border-border/30">
                <p className="text-xs text-text font-mono truncate" title={workingDir}>
                  {workingDir}
                </p>
              </div>
            </div>
          ) : (
            <div className="mb-6 px-4 py-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
              <div className="flex items-center gap-2 justify-center">
                <AlertCircle className="w-4 h-4 text-yellow-400" />
                <span className="text-sm text-yellow-400">Aucun dossier configuré</span>
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
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
            <div className="mt-4 flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400">{error}</span>
            </div>
          )}
        </motion.div>
      </div>

      {/* Footer */}
      <div className="flex justify-between pt-4 border-t border-border/30">
        <Button variant="ghost" onClick={onBack}>
          Retour
        </Button>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={onNext}>
            Passer
          </Button>
          <Button
            variant="primary"
            onClick={onNext}
            disabled={!workingDir}
            title={!workingDir ? 'Sélectionne un dossier ou clique sur "Passer"' : undefined}
          >
            Continuer
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
