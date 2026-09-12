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
import { Alerte } from '../ui/Alerte';
import { Carte } from '../ui/Carte';

interface WorkingDirStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function WorkingDirStep({ onNext, onBack }: WorkingDirStepProps) {
  const [workingDir, setWorkingDir] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // B-535 : un dossier disparu et une lecture impossible ne sont ni « configuré » ni « aucun ».
  const [dossierDisparu, setDossierDisparu] = useState(false);
  const [lectureImpossible, setLectureImpossible] = useState(false);

  // Load initial state
  useEffect(() => {
    async function loadState() {
      try {
        const workingDirData = await api.getWorkingDirectory();
        setWorkingDir(workingDirData?.path || null);
        setDossierDisparu(Boolean(workingDirData?.path) && workingDirData.exists === false);
        setLectureImpossible(false);
      } catch (err) {
        console.error('Failed to load working directory:', err);
        setLectureImpossible(true);
      } finally {
        setLoading(false);
      }
    }
    loadState();
  }, []);

  async function handleSelectDir() {
    let selected: string | string[] | null;
    try {
      selected = await open({
        directory: true,
        multiple: false,
      });
    } catch (err) {
      // Le pont natif n'a pas répondu. Son exception dit « Cannot read
      // properties of undefined (reading 'invoke') » : vrai pour qui lit du
      // JavaScript, inutile pour qui cherche son dossier.
      console.error('Ouverture du sélecteur de dossier impossible:', err);
      setError("La fenêtre de choix du dossier ne s’est pas ouverte. Redémarre THÉRÈSE, puis réessaie.");
      return;
    }

    if (!selected || typeof selected !== 'string') return;

    setSaving(true);
    setError(null);
    try {
      const result = await api.setWorkingDirectory(selected);
      setWorkingDir(result.path);
    } catch (err) {
      // Le serveur refuse en anglais (« Path does not exist ») : c'est un
      // message de journal, pas un message d'écran.
      console.error('Enregistrement du dossier de travail impossible:', err);
      setError('Ce dossier n’a pas pu être retenu. Vérifie qu’il existe toujours et qu’il t’est accessible, puis réessaie.');
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
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent-tint">
          <FolderOpen className="h-5 w-5 text-accent" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-text">Dossier de travail</h2>
          <p className="text-sm text-text-muted">Où se trouvent tes fichiers de travail ?</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="w-full max-w-md"
        >
          {/* Icon */}
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-accent-tint">
            <FolderOpen className="h-10 w-10 text-accent" />
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
          {lectureImpossible ? (
            <Alerte ton="attention" className="mb-6 text-left" icone={<AlertCircle className="h-4 w-4 text-warning" />}>Configuration du dossier illisible : le serveur n’a pas répondu. Tu peux quand même en choisir un.</Alerte>
          ) : workingDir && dossierDisparu ? (
            <div className="mb-6">
              <Alerte ton="attention" className="text-left" icone={<AlertCircle className="h-4 w-4 text-warning" />}>Dossier configuré mais introuvable : choisis-en un autre.</Alerte>
              <Carte className="mt-2 p-3">
                <p className="text-xs text-text font-mono truncate" title={workingDir}>{workingDir}</p>
              </Carte>
            </div>
          ) : workingDir ? (
            <div className="mb-6">
              <div className="flex items-center gap-2 rounded-md border border-success/30 bg-[var(--color-success-tint)] px-4 py-3">
                <Check className="w-4 h-4 text-success" />
                <span className="text-sm text-success">Dossier configuré</span>
              </div>
              <Carte className="mt-2 p-3">
                <p className="text-xs text-text font-mono truncate" title={workingDir}>
                  {workingDir}
                </p>
              </Carte>
            </div>
          ) : (
            <Alerte ton="attention" className="mb-6 text-left" icone={<AlertCircle className="h-4 w-4 text-warning" />}>Aucun dossier configuré</Alerte>
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
            <Alerte className="mt-4 text-left" icone={<AlertCircle className="h-4 w-4 text-error" />}>{error}</Alerte>
          )}
        </motion.div>
      </div>

      {/* Footer */}
      <div className="flex flex-wrap justify-between gap-3 border-t border-border pt-4">
        <Button variant="ghost" onClick={onBack} data-testid="onboarding-prev-btn">
          Retour
        </Button>
        <div className="flex flex-wrap gap-3 max-[840px]:basis-full">
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
