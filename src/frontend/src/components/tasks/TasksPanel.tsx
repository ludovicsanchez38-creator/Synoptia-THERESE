/**
 * THÉRÈSE v2 - Tasks Panel
 *
 * Panel principal pour gérer les tâches.
 * Phase 3 - Tasks/Todos
 *
 * DA « Application affinée », lot 6 (11/09/2026) : l'en-tête, les filtres et
 * les états prennent la forme de la maquette `projets.html` en consommant les
 * primitives du lot 1. Mêmes données, mêmes états, mêmes destinations.
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, RefreshCw, Filter, AlertCircle } from 'lucide-react';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';
import { TaskList } from './TaskList';
import { TaskForm } from './TaskForm';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Segments } from '../ui/Segments';
import { Select } from '../ui/Select';
import { Squelette } from '../ui/Squelette';
import { useDemoMask } from '../../hooks';
import * as api from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';

interface TasksPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  standalone?: boolean;
}

const OPTIONS_STATUT = [
  { value: '', label: 'Tous les statuts' },
  { value: 'todo', label: 'À faire' },
  { value: 'in_progress', label: 'En cours' },
  { value: 'done', label: 'Terminé' },
  { value: 'cancelled', label: 'Annulé' },
];

const OPTIONS_PRIORITE = [
  { value: '', label: 'Toutes les priorités' },
  { value: 'urgent', label: 'Urgent' },
  { value: 'high', label: 'Haute' },
  { value: 'medium', label: 'Moyenne' },
  { value: 'low', label: 'Basse' },
];

/** Trois rangées muettes pendant le premier chargement (§ 8 du design). */
function RangeesSquelette() {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <div key={i} aria-hidden="true" className="flex gap-3 items-center px-4 py-3 border-t border-border">
          <Squelette largeur="w-8" classeBarre="h-8 rounded-sm" />
          <div className="flex-1 min-w-0 flex flex-col gap-2">
            <Squelette largeur="w-[60%]" />
            <Squelette largeur="w-[40%]" />
          </div>
        </div>
      ))}
    </>
  );
}

export function TasksPanel({ isOpen, onClose, standalone = false }: TasksPanelProps) {
  const {
    tasks,
    viewMode,
    filterStatus,
    filterPriority,
    filterProjectId,
    isTaskFormOpen,
    setTasks,
    setCurrentTask,
    setIsTaskFormOpen,
    setViewMode,
    setFilterStatus,
    setFilterPriority,
    setFilterProjectId,
  } = useTaskStore();

  const { enabled: demoEnabled, populateMap } = useDemoMask();

  const hasCachedTasks = tasks.length > 0;
  const [loading, setLoading] = useState(!hasCachedTasks);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  // BUG-118 : filtres par projet (déjà supporté côté store/backend, UI manquante)
  // et par tag (filtré côté client, absent de l'API tâches).
  const [projects, setProjects] = useState<api.Project[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [filterTag, setFilterTag] = useState<string | null>(null);

  const effectiveOpen = standalone || isOpen;

  // Load tasks on mount
  useEffect(() => {
    if (effectiveOpen) {
      loadTasks();
    }
  }, [effectiveOpen, filterStatus, filterPriority, filterProjectId, filterTag]);

  // BUG-118 : liste des projets pour le filtre par projet
  useEffect(() => {
    if (!effectiveOpen) return;
    api.listProjects().then(setProjects).catch(() => setProjects([]));
  }, [effectiveOpen]);

  // Populate demo replacement map when demo mode is enabled
  useEffect(() => {
    if (!effectiveOpen || !demoEnabled) return;

    Promise.all([api.listContacts(), api.listProjects()])
      .then(([contacts, projects]) => {
        populateMap(contacts, projects);
      })
      .catch((err) => {
        console.error('Failed to load contacts/projects for demo mask:', err);
      });
  }, [effectiveOpen, demoEnabled, populateMap]);

  async function loadTasks() {
    if (!hasCachedTasks) setLoading(true);
    setError(null);

    try {
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (filterPriority) params.priority = filterPriority;
      if (filterProjectId) params.project_id = filterProjectId;

      const result = await api.listTasks(params);
      // BUG-118 : tags disponibles calculés sur le résultat serveur (avant filtre
      // tag), puis filtrage tag côté client (l'API tâches ne connaît pas les tags).
      setAvailableTags([...new Set(result.flatMap((t) => t.tags ?? []))].sort());
      const visible = filterTag
        ? result.filter((t) => (t.tags ?? []).includes(filterTag))
        : result;
      setTasks(visible);
    } catch (err: any) {
      console.error('Failed to load tasks:', err);
      // B-532 : un échec de rechargement se dit même avec une liste en cache,
      // qui peut être périmée.
      setError(hasCachedTasks ? 'Impossible de rafraîchir les tâches : la liste affichée peut être périmée.' : 'Impossible de charger les tâches');
    } finally {
      setLoading(false);
    }
  }

  function handleNewTask() {
    setCurrentTask(null);
    setIsTaskFormOpen(true);
  }

  if (!effectiveOpen) return null;

  const tasksHeader = (
    <div className="flex flex-wrap items-end gap-3 px-4 pt-4 pb-2">
      <div className="min-w-0">
        {/* B-241 : la coque `PrototypeUnifiedViewCanvas` pose déjà le titre de
            la vue, et en fait le nom accessible de la région. Ce libellé reste
            visible mais n'est plus un titre : deux titres de même texte, c'est
            un plan de page qui ment. */}
        <p className="text-lg font-semibold text-text">Tâches</p>
        <p className="text-sm text-text-muted">{tasks.length} tâche{tasks.length > 1 ? 's' : ''}</p>
      </div>

      <div className="ml-auto flex flex-wrap items-center gap-2 max-[840px]:basis-full max-[840px]:ml-0">
        {/* Lot 6 : la bascule de vue est un groupe de segments nommé. Les ids
            du store ne bougent pas ; les libellés sont ceux de la maquette. */}
        <Segments
          label="Vue des tâches"
          options={[
            { id: 'kanban', label: 'Colonnes' },
            { id: 'list', label: 'Liste' },
          ]}
          valeur={viewMode}
          onChange={(id) => setViewMode(id as 'kanban' | 'list')}
        />

        {/* B-209 : une commande réduite à son icône n'a aucun nom à annoncer.
            Le libellé va sur le bouton, pas sur l'icône décorative. */}
        <Button
          variant="secondary"
          size="md"
          aria-label="Filtrer les tâches"
          aria-expanded={showFilters}
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="h-[18px] w-[18px] mr-2" />
          Filtrer
        </Button>

        <Button variant="ghost" size="icon" aria-label="Rafraîchir les tâches" onClick={loadTasks}>
          <RefreshCw className="h-[18px] w-[18px]" />
        </Button>

        <Button variant="primary" size="md" onClick={handleNewTask}>
          <Plus className="h-[18px] w-[18px] mr-2" />
          Nouvelle tâche
        </Button>

        {!standalone && (
          <Button variant="ghost" size="icon" aria-label="Fermer les tâches" onClick={onClose}>
            <X className="h-[18px] w-[18px]" />
          </Button>
        )}
      </div>
    </div>
  );

  const tasksFilters = showFilters ? (
    <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b border-border">
      <Select
        aria-label="Filtrer par statut"
        value={filterStatus || ''}
        onChange={(e) => setFilterStatus(e.target.value || null)}
        options={OPTIONS_STATUT}
        className="w-auto"
      />

      <Select
        aria-label="Filtrer par priorité"
        value={filterPriority || ''}
        onChange={(e) => setFilterPriority(e.target.value || null)}
        options={OPTIONS_PRIORITE}
        className="w-auto"
      />

      {projects.length > 0 && (
        <Select
          aria-label="Filtrer par projet"
          value={filterProjectId || ''}
          onChange={(e) => setFilterProjectId(e.target.value || null)}
          options={[
            { value: '', label: 'Tous les projets' },
            ...projects.map((p) => ({ value: p.id, label: p.name })),
          ]}
          className="w-auto"
        />
      )}

      {availableTags.length > 0 && (
        <Select
          aria-label="Filtrer par étiquette"
          value={filterTag || ''}
          onChange={(e) => setFilterTag(e.target.value || null)}
          options={[
            { value: '', label: 'Tous les tags' },
            ...availableTags.map((t) => ({ value: t, label: t })),
          ]}
          className="w-auto"
        />
      )}

      {(filterStatus || filterPriority || filterProjectId || filterTag) && (
        <Button
          variant="ghost"
          size="md"
          onClick={() => {
            setFilterStatus(null);
            setFilterPriority(null);
            setFilterProjectId(null);
            setFilterTag(null);
          }}
        >
          Réinitialiser
        </Button>
      )}
    </div>
  ) : null;

  const tasksContent = (
    <>
      {/* B-532 et revue v4 du design : le bandeau est un FRÈRE de la cascade,
          jamais une branche qui l'exclut - sinon un échec de rafraîchissement
          effacerait le formulaire ouvert ou la liste en cache. */}
      {error && (
        <Alerte className="mx-4 mt-2" icone={<AlertCircle className="h-[18px] w-[18px]" />}>
          {error}
        </Alerte>
      )}

      <div className="flex-1 overflow-hidden">
        {loading ? (
          <RangeesSquelette />
        ) : isTaskFormOpen ? (
          <TaskForm />
        ) : viewMode === 'kanban' ? (
          <TaskKanban />
        ) : (
          <TaskList />
        )}
      </div>
    </>
  );

  // Mode standalone : pleine page
  if (standalone) {
    // flex-1 min-h-0, pas h-full : la back-bar « Chat » du conteneur de vue
    // ferait déborder le panneau de sa hauteur (cf. bug EmailPanel 11/06).
    return (
      <div className="flex-1 min-h-0 flex flex-col bg-bg" data-testid="tasks-panel">
        {tasksHeader}
        {tasksFilters}
        {tasksContent}
      </div>
    );
  }

  // Mode modal
  return (
    <AnimatePresence>
      <div className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center`}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          // Lot 6 : le voile de la coque DA, pas une palette Tailwind brute.
          className="absolute inset-0 bg-text/35 backdrop-blur-md"
          onClick={onClose}
        />

        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label="Tâches"
          data-testid="tasks-panel"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full h-full max-w-7xl max-h-[90vh] mx-4 bg-surface border border-border rounded-md shadow-lg overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {tasksHeader}
          {tasksFilters}
          {tasksContent}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
