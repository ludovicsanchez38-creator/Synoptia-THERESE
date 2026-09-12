/**
 * THÉRÈSE v2 - DocumentCreateModal (Atelier documentaire, D2)
 *
 * Modale légère de création de document : titre + brief + projet lié
 * optionnel. Les projets sont chargés via l'API Mémoire existante
 * (`listProjects`), même pattern que ProjectModal pour les contacts.
 * Confirmation API AVANT toute fermeture (documentStore.createDocument ne
 * mute qu'après succès - anti-faux-succès, cf. commentaire du store D1).
 */
import { useEffect, useRef, useState } from 'react';
import { X, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { useDocumentStore } from '../../stores/documentStore';
import { listProjects, type Project } from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';

interface DocumentCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Appelé après création réussie, avant onClose. */
  onCreated?: (documentId: string) => void;
}

export function DocumentCreateModal({ isOpen, onClose, onCreated }: DocumentCreateModalProps) {
  const createDocument = useDocumentStore((s) => s.createDocument);
  const clearError = useDocumentStore((s) => s.clearError);

  const [title, setTitle] = useState('');
  const [brief, setBrief] = useState('');
  const [projectId, setProjectId] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  // État dégradé : l'API projets a échoué. Affiché discrètement à la place du
  // select (le document reste créable sans projet lié) - pas d'échec muet.
  const [projectsUnavailable, setProjectsUnavailable] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la pile unifiée (cascade Échap de la coque / escapeStack du parent).
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isOpen });

  useEffect(() => {
    if (!isOpen) return;
    setTitle('');
    setBrief('');
    setProjectId('');
    setFormError(null);
    setProjectsUnavailable(false);
    clearError();

    let cancelled = false;
    setLoadingProjects(true);
    listProjects()
      .then((data) => {
        if (!cancelled) setProjects(data);
      })
      .catch((err) => {
        console.error('Impossible de charger les projets :', err);
        if (!cancelled) {
          setProjects([]);
          setProjectsUnavailable(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingProjects(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, clearError]);

  async function handleSubmit() {
    if (!title.trim()) {
      setFormError('Le titre du document est requis');
      return;
    }

    setSaving(true);
    setFormError(null);

    const created = await createDocument({
      title: title.trim(),
      brief: brief.trim(),
      project_id: projectId || null,
    });

    setSaving(false);

    if (created) {
      onCreated?.(created.id);
      onClose();
    } else {
      setFormError(useDocumentStore.getState().error || 'Impossible de créer le document.');
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className={`fixed inset-0 bg-text/35 backdrop-blur-sm ${Z_LAYER.MODAL}`}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Nouveau document"
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[calc(100%-2rem)] max-w-lg bg-surface border border-border rounded-md ${Z_LAYER.MODAL} max-h-[85vh] overflow-hidden flex flex-col`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-sm bg-accent-tint border border-accent flex items-center justify-center">
                  <FileText className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">Nouveau document</h2>
                  <p className="text-sm text-text-muted">Proposition, dossier ou rapport structuré</p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose} aria-label="Fermer">
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <FormField label="Titre" htmlFor="document-title" required>
                <Input
                  id="document-title"
                  type="text"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    setFormError(null);
                  }}
                  placeholder="Proposition commerciale - Client X"
                  autoFocus
                />
              </FormField>

              <FormField label="Brief" htmlFor="document-brief">
                <Textarea
                  id="document-brief"
                  value={brief}
                  onChange={(e) => setBrief(e.target.value)}
                  placeholder="Objectif, contexte, destinataire..."
                  rows={4}
                />
              </FormField>

              <FormField label="Projet lié (optionnel)" htmlFor="document-project">
                {projectsUnavailable ? (
                  <p className="px-4 py-2.5 bg-surface-2 border border-border rounded-sm text-sm text-text-muted">
                    Projets indisponibles - le document sera créé sans projet lié.
                  </p>
                ) : (
                  <Select
                    id="document-project"
                    value={projectId}
                    onChange={(e) => setProjectId(e.target.value)}
                    disabled={loadingProjects}
                    options={[
                      { value: '', label: 'Aucun projet' },
                      ...projects.map((project) => ({ value: project.id, label: project.name })),
                    ]}
                  />
                )}
                {loadingProjects && (
                  <p role="status" className="text-sm text-text-muted flex items-center gap-1">
                    <Spinner taille="ligne" />
                    Chargement des projets...
                  </p>
                )}
              </FormField>

              {formError && (
                <Alerte>{formError}</Alerte>
              )}
            </div>

            {/* Footer */}
            <div className="flex flex-wrap items-center justify-end gap-3 px-6 py-4 border-t border-border/50 shrink-0 max-[840px]:justify-stretch [&>button]:max-[840px]:flex-1">
              <Button variant="ghost" onClick={onClose}>
                Annuler
              </Button>
              <Button variant="primary" onClick={handleSubmit} disabled={saving}>
                {saving ? (
                  <>
                    <Spinner taille="bouton" className="mr-2" />
                    Création...
                  </>
                ) : (
                  'Créer'
                )}
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
