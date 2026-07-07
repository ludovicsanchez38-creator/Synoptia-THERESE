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
import { X, FileText, Loader2, Briefcase } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { useDocumentStore } from '../../stores/documentStore';
import { listProjects, type Project } from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';

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
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la pile unifiée (resolveEscape / escapeStack du parent).
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isOpen });

  useEffect(() => {
    if (!isOpen) return;
    setTitle('');
    setBrief('');
    setProjectId('');
    setFormError(null);
    clearError();

    let cancelled = false;
    setLoadingProjects(true);
    listProjects()
      .then((data) => {
        if (!cancelled) setProjects(data);
      })
      .catch((err) => {
        console.error('Impossible de charger les projets :', err);
        if (!cancelled) setProjects([]);
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
            className={`fixed inset-0 bg-black/60 backdrop-blur-sm ${Z_LAYER.MODAL}`}
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
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-surface border border-border rounded-xl shadow-2xl ${Z_LAYER.MODAL} max-h-[85vh] overflow-hidden flex flex-col`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-[6px] bg-accent-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
                  <FileText className="w-5 h-5 text-accent-cyan" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">Nouveau document</h2>
                  <p className="text-xs text-text-muted">Proposition, dossier ou rapport structuré</p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose} aria-label="Fermer">
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="space-y-2">
                <label htmlFor="document-title" className="text-sm text-text-muted">
                  Titre <span className="text-error">*</span>
                </label>
                <input
                  id="document-title"
                  type="text"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    setFormError(null);
                  }}
                  placeholder="Proposition commerciale - Client X"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="document-brief" className="text-sm text-text-muted">
                  Brief
                </label>
                <textarea
                  id="document-brief"
                  value={brief}
                  onChange={(e) => setBrief(e.target.value)}
                  placeholder="Objectif, contexte, destinataire..."
                  rows={4}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="document-project" className="text-sm text-text-muted flex items-center gap-2">
                  <Briefcase className="w-4 h-4" />
                  Projet lié (optionnel)
                </label>
                <select
                  id="document-project"
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  disabled={loadingProjects}
                >
                  <option value="">Aucun projet</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
                {loadingProjects && (
                  <p className="text-xs text-text-muted flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Chargement des projets...
                  </p>
                )}
              </div>

              {formError && (
                <div className="flex items-center gap-2 px-3 py-2 bg-error/10 border border-error/20 rounded-lg">
                  <span className="text-sm text-error">{formError}</span>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border/50 shrink-0">
              <Button variant="ghost" onClick={onClose}>
                Annuler
              </Button>
              <Button variant="primary" onClick={handleSubmit} disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
