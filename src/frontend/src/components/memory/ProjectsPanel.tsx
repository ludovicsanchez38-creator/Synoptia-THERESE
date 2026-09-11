/**
 * THÉRÈSE v2 - ProjectsPanel (vue Projets dédiée)
 *
 * Restaure la surface de gestion des projets perdue lors de la refonte nav 0.20
 * (BUG-104 : le bouton « Projet » du header ouvrait les Contacts, et le kanban
 * des projets n'était plus rendu nulle part). Liste + kanban par statut avec
 * drag & drop, création/édition via ProjectModal, suppression avec confirmation.
 *
 * DA « Application affinée », lot 6 (11/09/2026) : en-tête sans pastille,
 * quatre états sur les primitives, pleine largeur de la coque au lieu d'une
 * largeur maison, comme les autres panneaux (CRM, Factures, Agenda, Mémoire).
 * Pas « la colonne de 56 rem » : `--container-colonne` n'est consommé que par
 * la colonne de conversation (`ConversationCanvasPrototype.tsx:1688`), l'autre
 * branche du ternaire, et la coque ne borne rien
 * (`PrototypeUnifiedViewCanvas.tsx:50`).
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, Plus } from 'lucide-react';
import * as api from '../../services/api';
import type { Project } from '../../services/api';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte } from '../ui/Carte';
import { EtatVide } from '../ui/EtatVide';
import { Squelette } from '../ui/Squelette';
import { Z_LAYER } from '../../styles/z-layers';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { useStatusStore } from '../../stores/statusStore';
import { ProjectsKanban } from './ProjectsKanban';
import { ProjectModal } from './ProjectModal';

/**
 * B-098 : plafond DUR du GET projets (`limit` borné à 200 côté serveur, 201
 * est refusé en 422). Atteint, l'écran ne peut pas connaître le nombre réel :
 * il le dit, au lieu de présenter 200 comme un total. Même motif que
 * PLAFOND_CONTACTS et que les fichiers de projet.
 */
const PLAFOND_PROJETS = 200;

export function ProjectsPanel() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [listeTronquee, setListeTronquee] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);
  // B-402 : la confirmation piège le focus comme ProjectModal ; Tab fuyait vers le kanban sous le voile.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: Boolean(deleteTarget) });
  const addNotification = useStatusStore((s) => s.addNotification);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listProjects(0, PLAFOND_PROJETS);
      setProjects(data);
      setListeTronquee(data.length >= PLAFOND_PROJETS);
      setError(null);
    } catch (err) {
      console.error('Failed to load projects:', err);
      // Le drapeau tombe avec la liste : rien ne doit survivre pour décrire
      // des données qui ne sont plus là (leçon B-009 côté factures).
      setListeTronquee(false);
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
  // invisibles pour cascade Échap de la coque → Échap éjectait la vue SOUS la modale. On les
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
        // B-428 : la carte revenait en place sans un mot.
        addNotification({ type: 'error', title: 'Statut non modifié', message: 'Le serveur a refusé le changement de statut ; la carte est revenue à sa place.' });
        load();
      }
    },
    [load, addNotification]
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
      addNotification({ type: 'error', title: 'Projet non supprimé', message: 'Le serveur a refusé la suppression ; le projet est toujours là.' });
      load();
    }
  }, [deleteTarget, load, addNotification]);

  return (
    <div className="flex-1 min-w-0 overflow-y-auto">
      <div className="px-4 py-4">
        {/* En-tête */}
        <div className="flex flex-wrap items-end gap-3 mb-3">
          <div className="min-w-0">
            {/* B-241 : la coque `PrototypeUnifiedViewCanvas` pose déjà le titre de
                la vue, et en fait le nom accessible de la région. Ce libellé reste
                visible mais n'est plus un titre : deux titres de même texte, c'est
                un plan de page qui ment. */}
            <p className="text-lg font-semibold text-text">Projets</p>
            <p className="text-sm text-text-muted">
              {projects.length}{listeTronquee ? '+' : ''} projet{projects.length > 1 ? 's' : ''}
            </p>
          </div>
          <Button variant="primary" size="md" className="ml-auto" onClick={handleNew}>
            <Plus className="h-[18px] w-[18px] mr-2" />
            Nouveau projet
          </Button>
        </div>

        {/* La troncature n'est pas une erreur : la liste affichée est juste,
            elle est seulement incomplète. Pas d'`Alerte`, réservée à la panne. */}
        {listeTronquee && (
          <p role="alert" className="text-sm text-warning px-4 py-2 bg-[var(--color-warning-tint)] rounded-sm mb-3">
            Liste incomplète : seuls les {PLAFOND_PROJETS} premiers projets
            sont affichés, d'autres existent.
          </p>
        )}

        {/* Contenu */}
        {loading ? (
          <div>
            {[0, 1, 2].map((i) => (
              <div key={i} aria-hidden="true" className="flex gap-3 items-center px-4 py-3 border-t border-border">
                <Squelette largeur="w-8" classeBarre="h-8 rounded-sm" />
                <div className="flex-1 min-w-0 flex flex-col gap-2">
                  <Squelette largeur="w-[60%]" />
                  <Squelette largeur="w-[40%]" />
                </div>
              </div>
            ))}
            {/* Frère des rangées muettes : coller ce texte dans l'une d'elles
                ferait tomber l'annonce. */}
            <p role="status" className="px-4 py-3 text-sm text-text-muted">
              Chargement des projets…
            </p>
          </div>
        ) : error ? (
          <Alerte
            titre={error}
            icone={<AlertCircle className="h-[18px] w-[18px]" />}
            action={(
              <Button variant="secondary" size="md" onClick={load}>
                Réessayer
              </Button>
            )}
          />
        ) : projects.length === 0 ? (
          /* Le geste « Nouveau projet » est déjà en tête : l'état vide ne le
             redouble pas. */
          <EtatVide titre="Aucun projet" />
        ) : (
          <Carte as="section" className="overflow-hidden">
            <ProjectsKanban
              projects={projects}
              onSelect={handleSelect}
              onDelete={setDeleteTarget}
              onStatusChange={handleStatusChange}
            />
          </Carte>
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
          className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center bg-text/35 p-4`}
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-project-title"
          ref={dialogRef}
        >
          <div className="w-full max-w-sm rounded-md border border-border bg-surface p-5 shadow-lg">
            <h2 id="delete-project-title" className="text-base font-semibold text-text">
              Supprimer le projet ?
            </h2>
            <p className="text-sm text-text-muted mt-2">
              « {deleteTarget.name} » sera supprimé. Cette action est définitive.
            </p>
            <div className="flex justify-end gap-2 mt-5">
              <Button variant="ghost" size="md" autoFocus onClick={() => setDeleteTarget(null)}>
                Annuler
              </Button>
              <Button variant="danger" size="md" onClick={confirmDelete}>
                Supprimer
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
