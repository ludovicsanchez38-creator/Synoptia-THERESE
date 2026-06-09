/**
 * THÉRÈSE v2 - ProjectsPanel (vue Projets dédiée)
 *
 * Restaure la surface de gestion des projets perdue lors de la refonte nav 0.20
 * (BUG-104 : le bouton « Projet » du header ouvrait les Contacts, et le kanban
 * des projets n'était plus rendu nulle part). Liste + kanban par statut avec
 * drag & drop, création/édition via ProjectModal, suppression avec confirmation.
 */

import { useCallback, useEffect, useState } from 'react';
import { Plus, Loader2, Briefcase } from 'lucide-react';
import * as api from '../../services/api';
import type { Project } from '../../services/api';
import { Button } from '../ui/Button';
import { Z_LAYER } from '../../styles/z-layers';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { ProjectsKanban } from './ProjectsKanban';
import { ProjectModal } from './ProjectModal';

export function ProjectsPanel() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listProjects(0, 200);
      setProjects(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError('Impossible de charger les projets.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // F2 (revue) : la modale projet GLOBALE (⌘K « Ajouter un projet », palette) est
  // pilotée par panelStore, hors de cette vue. On se resynchronise quand elle signale
  // un changement, sinon une création via ⌘K n'apparaîtrait pas tant qu'on reste ici.
  useEffect(() => {
    const onChanged = () => load();
    window.addEventListener('therese:memory-changed', onChanged);
    return () => window.removeEventListener('therese:memory-changed', onChanged);
  }, [load]);

  // F1 (revue) : nos overlays sont en state local (non pilotés par panelStore), donc
  // invisibles pour resolveEscape → Échap éjectait la vue SOUS la modale. On les
  // enregistre sur la pile Échap unifiée (LIFO) tant qu'ils sont ouverts.
  useEffect(() => {
    if (!deleteTarget) return;
    return pushEscapeHandler(() => setDeleteTarget(null));
  }, [deleteTarget]);

  useEffect(() => {
    if (!modalOpen) return;
    return pushEscapeHandler(() => {
      setModalOpen(false);
      setEditing(null);
    });
  }, [modalOpen]);

  const handleNew = useCallback(() => {
    setEditing(null);
    setModalOpen(true);
  }, []);

  const handleSelect = useCallback((project: Project) => {
    setEditing(project);
    setModalOpen(true);
  }, []);

  const handleSaved = useCallback(() => {
    setModalOpen(false);
    setEditing(null);
    load();
  }, [load]);

  const handleStatusChange = useCallback(
    async (projectId: string, newStatus: string) => {
      // Optimiste : on déplace la carte tout de suite, on resynchronise si échec.
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? { ...p, status: newStatus } : p))
      );
      try {
        await api.updateProject(projectId, { status: newStatus });
      } catch (err) {
        console.error('Failed to update project status:', err);
        load();
      }
    },
    [load]
  );

  const confirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    const id = deleteTarget.id;
    setDeleteTarget(null);
    try {
      await api.deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error('Failed to delete project:', err);
      load();
    }
  }, [deleteTarget, load]);

  return (
    <div className="flex-1 min-w-0 overflow-y-auto">
      <div className="max-w-[760px] mx-auto px-5 py-6">
        {/* En-tête */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-lg grid place-items-center bg-accent-cyan/10 text-accent-cyan">
              <Briefcase className="w-5 h-5" />
            </span>
            <div>
              <h1 className="text-lg font-bold text-text leading-tight">Projets</h1>
              <p className="text-xs text-text-muted">
                {projects.length} projet{projects.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <Button variant="primary" size="sm" onClick={handleNew}>
            <Plus className="w-4 h-4 mr-1.5" />
            Nouveau projet
          </Button>
        </div>

        {/* Contenu */}
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-sm text-text-muted">
            <Loader2 className="w-5 h-5 animate-spin text-accent-cyan" /> Chargement des projets…
          </div>
        ) : error ? (
          <div className="py-10 text-center">
            <p className="text-sm text-text-muted">{error}</p>
            <Button variant="ghost" size="sm" className="mt-3" onClick={load}>
              Réessayer
            </Button>
          </div>
        ) : (
          <div className="rounded-xl border border-border/40 bg-surface/40 overflow-hidden">
            <ProjectsKanban
              projects={projects}
              onSelect={handleSelect}
              onDelete={setDeleteTarget}
              onStatusChange={handleStatusChange}
            />
          </div>
        )}
      </div>

      {/* Modale création / édition */}
      <ProjectModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSaved={handleSaved}
        project={editing}
      />

      {/* Confirmation de suppression */}
      {deleteTarget && (
        <div
          className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center bg-black/50 p-4`}
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-project-title"
        >
          <div className="w-full max-w-sm rounded-xl border border-border bg-surface p-5 shadow-xl">
            <h2 id="delete-project-title" className="text-base font-semibold text-text">
              Supprimer le projet ?
            </h2>
            <p className="text-sm text-text-muted mt-2">
              « {deleteTarget.name} » sera supprimé. Cette action est définitive.
            </p>
            <div className="flex justify-end gap-2 mt-5">
              <Button variant="ghost" size="sm" autoFocus onClick={() => setDeleteTarget(null)}>
                Annuler
              </Button>
              <Button variant="danger" size="sm" onClick={confirmDelete}>
                Supprimer
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
