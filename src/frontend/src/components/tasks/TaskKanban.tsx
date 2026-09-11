/**
 * THÉRÈSE v2 - Task Kanban View
 *
 * Vue Kanban avec colonnes Todo/In Progress/Done.
 * Drag & Drop via @dnd-kit.
 * Phase 3 - Tasks/Todos
 *
 * DA « Application affinée », lot 6 (11/09/2026) : grille de trois colonnes
 * (deux sous 1023 px, sur deux rangées `1fr`), têtes en `Etiquette`, priorité
 * en barre nommée, commandes dans le flux de la carte.
 */

import { useMemo, useState } from 'react';
import { CheckCircle2, Circle, Clock, GripVertical } from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  useSensor,
  useSensors,
  PointerSensor,
  KeyboardSensor,
  useDroppable,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useTaskStore } from '../../stores/taskStore';
import type { Task } from '../../services/api';
import * as api from '../../services/api';
import { useDemoMask } from '../../hooks';
import { isPastParisCivilDate } from '../../lib/civilDate';
import { accessibiliteGlisserDeposer } from '../../lib/accessibiliteGlisserDeposer';
import { useStatusStore } from '../../stores/statusStore';
import { Etiquette, type TonEtiquette } from '../ui/Etiquette';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';
import { CLASSE_BARRE_PRIORITE, barrePriorite } from './prioriteBarre';

const COLUMNS: { id: string; label: string; ton: TonEtiquette }[] = [
  { id: 'todo', label: 'À faire', ton: 'neutre' },
  { id: 'in_progress', label: 'En cours', ton: 'info' },
  { id: 'done', label: 'Terminé', ton: 'succes' },
];

export function TaskKanban() {
  const { tasks, searchQuery, setCurrentTask, setIsTaskFormOpen, updateTask } = useTaskStore();
  const { maskText } = useDemoMask();
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor)
  );

  // Group tasks by status
  const tasksByStatus = useMemo(() => {
    const filtered = searchQuery
      ? tasks.filter((t) =>
          t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          t.description?.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : tasks;

    const groups: Record<string, Task[]> = {
      todo: [],
      in_progress: [],
      done: [],
    };

    filtered.forEach((task) => {
      if (groups[task.status]) {
        groups[task.status].push(task);
      }
    });

    return groups;
  }, [tasks, searchQuery]);

  async function handleStatusChange(taskId: string, newStatus: string) {
    try {
      const updated = await api.updateTask(taskId, { status: newStatus });
      updateTask(taskId, updated);
    } catch (err) {
      console.error('Failed to update task status:', err);
      // B-524 : un refus du serveur se dit, la carte ne revient plus sans explication.
      useStatusStore.getState().addNotification({ type: 'error', title: 'Tâche non mise à jour', message: 'Le changement n’a pas été enregistré. Réessaie dans un instant.' });
    }
  }

  function handleTaskClick(taskId: string) {
    setCurrentTask(taskId);
    setIsTaskFormOpen(true);
  }

  function handleDragStart(event: DragStartEvent) {
    const taskId = event.active.id as string;
    const task = tasks.find((t) => t.id === taskId);
    if (task) setActiveTask(task);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveTask(null);

    const { active, over } = event;
    if (!over) return;

    const taskId = active.id as string;

    // Determine the target column
    let targetColumn: string | null = null;

    // Check if dropped on a column directly
    const columnIds = COLUMNS.map((c) => c.id);
    if (columnIds.includes(over.id as string)) {
      targetColumn = over.id as string;
    } else {
      // Dropped on a task card - find which column it belongs to
      for (const col of columnIds) {
        if (tasksByStatus[col]?.some((t) => t.id === over.id)) {
          targetColumn = col;
          break;
        }
      }
    }

    if (!targetColumn) return;

    // Find current task status
    const currentTask = tasks.find((t) => t.id === taskId);
    if (!currentTask || currentTask.status === targetColumn) return;

    // Update the status
    handleStatusChange(taskId, targetColumn);
  }

  // B-217 : sans ce bloc, dnd-kit sert ses consignes ANGLAISES par défaut et
  // annonce les objets par leur identifiant technique. `over.id` désigne
  // aussi bien une carte qu'une colonne : les deux passent par ici.
  const accessibilite = accessibiliteGlisserDeposer((id) =>
    tasks.find((task) => task.id === id)?.title
      ?? COLUMNS.find((column) => column.id === id)?.label
      ?? null,
  );

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setActiveTask(null)}
      accessibility={accessibilite}
    >
      {/* Lot 6 : la maquette s'arrête à DEUX colonnes sous 1023 px, jamais une.
          Les deux rangées `1fr` gardent « Terminé » dans le viewport et
          laissent les listes défiler chacune de son côté. */}
      <div className="grid grid-cols-3 max-[1023px]:grid-cols-2 max-[1023px]:grid-rows-2 max-[1023px]:auto-rows-fr gap-3 p-4 h-full min-h-0">
        {COLUMNS.map((column) => (
          <DroppableColumn key={column.id} column={column} count={tasksByStatus[column.id].length}>
            <SortableContext
              items={tasksByStatus[column.id].map((t) => t.id)}
              strategy={verticalListSortingStrategy}
            >
              {tasksByStatus[column.id].length === 0 ? (
                <div className="flex items-center justify-center h-32">
                  <p className="text-sm text-text-muted">Aucune tâche</p>
                </div>
              ) : (
                tasksByStatus[column.id].map((task) => (
                  <SortableTaskCard
                    key={task.id}
                    task={task}
                    onClick={() => handleTaskClick(task.id)}
                    onStatusChange={(newStatus) => handleStatusChange(task.id, newStatus)}
                    maskTextFn={maskText}
                  />
                ))
              )}
            </SortableContext>
          </DroppableColumn>
        ))}
      </div>

      <DragOverlay>
        {activeTask && (
          <TaskCard
            task={activeTask}
            onClick={() => {}}
            onStatusChange={() => {}}
            isOverlay
            showDragHandle
            maskTextFn={maskText}
          />
        )}
      </DragOverlay>
    </DndContext>
  );
}

// =============================================================================
// DROPPABLE COLUMN
// =============================================================================

interface DroppableColumnProps {
  column: (typeof COLUMNS)[number];
  count: number;
  children: React.ReactNode;
}

function DroppableColumn({ column, count, children }: DroppableColumnProps) {
  const { isOver, setNodeRef } = useDroppable({ id: column.id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col gap-2 bg-surface-2 rounded-md p-2 min-h-0 transition-colors',
        isOver && 'ring-2 ring-ring/50 bg-accent-tint',
      )}
    >
      {/* Column Header. Le h3 reste : c'est le plan de l'écran, et la maquette
          l'écrit ainsi (`projets.html:66`). Police et graisse sont POSÉES, pas
          héritées : le socle donne au `h3` la display et 700 (`globals.css:607`
          et `:616`), la tête jumelle de `ProjectsKanban` est un `div` qui reste
          en police de corps à 400. Le compte suit la maquette
          (`.col h3 .compte{font-weight:500}`, `projets.html:12`). */}
      <h3 className="flex items-center gap-2 px-2 py-1 text-sm font-editorial tracking-[-0.01em]">
        <Etiquette ton={column.ton}>{column.label}</Etiquette>
        <span className="ml-auto text-sm font-medium tabular-nums text-text-muted">{count}</span>
      </h3>

      {/* Tasks. `p-1.5` : l'anneau du socle se dessine DEHORS (`outline: 3px`
          à `outline-offset: 2px`, `globals.css:618-621`), le conteneur
          `useSortable` d'une carte est focalisable, et `overflow-y-auto` rend
          l'axe horizontal découpant lui aussi. Sans marge ici, l'anneau est
          rogné à gauche, à droite, et en haut pour la première carte. Le `p-2`
          de la colonne est hors du conteneur qui découpe : il n'y peut rien. */}
      <div className="flex-1 min-h-0 overflow-y-auto space-y-2 p-1.5">{children}</div>
    </div>
  );
}

// =============================================================================
// SORTABLE TASK CARD (wraps TaskCard with drag handle)
// =============================================================================

interface SortableTaskCardProps {
  task: Task;
  onClick: () => void;
  onStatusChange: (newStatus: string) => void;
  maskTextFn?: (text: string) => string;
}

function SortableTaskCard({ task, onClick, onStatusChange, maskTextFn }: SortableTaskCardProps) {
  // B-209 : les commandes de la carte n'existaient que pour la souris
  // (`onMouseEnter` seul). Le focus clavier atterrit ICI - c'est ce conteneur
  // que `useSortable` rend focalisable - et pas sur la carte : brancher la
  // révélation plus bas ne déclencherait jamais rien.
  const [focusDansLaCarte, setFocusDansLaCarte] = useState(false);
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  // Même fix que le BUG-041 (ProjectsKanban) : les listeners couvrent toute
  // la carte, pas seulement la poignée - sinon attraper la carte par son
  // corps ne démarre aucun drag. Les clics simples (ouvrir, quick actions)
  // restent distingués du drag par l'activationConstraint (distance 8px).
  // B-750 : sans `setActivatorNodeRef`, `activatorNode.current` reste `null`
  // et la garde du KeyboardSensor (`event.target !== activator`, cf
  // `@dnd-kit/core/dist/core.esm.js`) ne s'applique JAMAIS : le capteur
  // écoutait tout le sous-arbre, si bien qu'Entrée ou Espace sur « Marquer
  // terminé » saisissait la carte et confisquait l'activation du bouton. Le
  // nœud activateur est l'enveloppe elle-même, celle qui porte les écouteurs
  // et le focus : la frappe partie d'elle ouvre bien un glisser, celle partie
  // d'une commande revient au bouton. Le PointerSensor, lui, n'a pas de
  // garde d'activateur : le glisser à la souris depuis le corps de la carte
  // (BUG-041, seuil de 8 px) reste intact.
  return (
    <div
      ref={(noeud) => { setNodeRef(noeud); setActivatorNodeRef(noeud); }}
      style={style}
      className="cursor-grab active:cursor-grabbing"
      {...attributes}
      {...listeners}
      onFocus={() => setFocusDansLaCarte(true)}
      onBlur={(event) => {
        // Passer d'une commande de la carte à l'autre ne referme rien :
        // sans cette garde, le premier Tab ferait disparaître sa cible.
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setFocusDansLaCarte(false);
        }
      }}
    >
      <TaskCard
        task={task}
        onClick={onClick}
        onStatusChange={onStatusChange}
        showDragHandle
        commandesRevelees={focusDansLaCarte}
        maskTextFn={maskTextFn}
      />
    </div>
  );
}

// =============================================================================
// TASK CARD
// =============================================================================

interface TaskCardProps {
  task: Task;
  onClick: () => void;
  onStatusChange: (newStatus: string) => void;
  isOverlay?: boolean;
  showDragHandle?: boolean;
  /** B-209 : révélation venue du clavier, en plus du survol souris. */
  commandesRevelees?: boolean;
  maskTextFn?: (text: string) => string;
}

function TaskCard({ task, onClick, onStatusChange, isOverlay, showDragHandle, commandesRevelees = false, maskTextFn }: TaskCardProps) {
  const [survol, setSurvol] = useState(false);
  const showActions = survol || commandesRevelees;

  const barre = barrePriorite(task.priority);

  const isOverdue = Boolean(
    task.due_date
      && isPastParisCivilDate(task.due_date)
      && !['done', 'cancelled'].includes(task.status),
  );
  const isDone = task.status === 'done';

  return (
    <div
      /* B-151 : repère par élément pour les protocoles (`qsa`). Pas sur la
         carte de survol du drag, qui doublerait le comptage. */
      data-testid={isOverlay ? undefined : 'task-item'}
      onMouseEnter={() => setSurvol(true)}
      onMouseLeave={() => setSurvol(false)}
      /* Pas de `transition-colors` : aucune couleur ne change. La maquette ne
         pose aucun `:hover` sur `.tache` (`projets.html:13`), et un
         `hover:bg-surface-2` fondrait la carte dans sa colonne, qui est
         justement en `bg-surface-2`. Le retour au survol reste la révélation
         des commandes. */
      className={cn(
        'relative bg-surface border border-border rounded-sm p-3 cursor-pointer',
        isOverlay && 'shadow-lg ring-2 ring-ring/30',
      )}
      onClick={onClick}
    >
      {/* Poignée (repère visuel : toute la carte est draggable) */}
      {showDragHandle && (
        <div className="absolute top-3 left-1 text-text-muted">
          <GripVertical className="w-4 h-4" />
        </div>
      )}

      <div className={showDragHandle ? 'pl-5' : ''}>
        <div className="flex items-start gap-2">
          {/* Lot 6 : la priorité est un aplat nommé, plus un mot. `role="img"`
              est obligatoire : sans rôle, l'`aria-label` n'expose rien. */}
          {barre && (
            <span role="img" aria-label={barre.nom} className={cn(CLASSE_BARRE_PRIORITE, barre.classe)} />
          )}

          <div className="min-w-0 flex-1">
            <h4 className={cn('font-semibold text-sm', isDone ? 'line-through text-text-muted' : 'text-text')}>
              {maskTextFn ? maskTextFn(task.title) : task.title}
            </h4>

            {/* Description. B-134 : corps de la carte, pas une métadonnée - cf TaskList. */}
            {task.description && (
              <p className="text-sm text-text-muted line-clamp-2 mt-1">{maskTextFn ? maskTextFn(task.description) : task.description}</p>
            )}

            {/* Pied : retard, échéance, étiquettes - les métadonnées de la maquette. */}
            {(isOverdue || task.due_date || (task.tags && task.tags.length > 0)) && (
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {isOverdue && <Etiquette ton="erreur">En retard</Etiquette>}

                {task.due_date && (
                  <span className="text-xs font-medium text-text-muted">
                    {new Date(task.due_date).toLocaleDateString('fr-FR', {
                      day: 'numeric',
                      month: 'short',
                    })}
                  </span>
                )}

                {task.tags && task.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 text-xs bg-accent-tint text-accent-cyan-ink rounded-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions. Lot 6 : la rangée vit dans le FLUX et reste montée,
            pour que la hauteur de la carte ne saute pas au survol. Cachée,
            elle l'est par `invisible` (pas `opacity-0`, interdit autour d'un
            bouton par focusVisibleSurActions ; pas `hidden`, qui reprendrait
            la hauteur) ET par `aria-hidden`, seul à la retirer de l'arbre
            d'accessibilité - jsdom n'applique aucun CSS. */}
        {!isOverlay && (
          <div
            aria-hidden={!showActions}
            className={cn(
              'flex items-center gap-1 mt-2',
              !showActions && 'invisible pointer-events-none',
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {task.status !== 'in_progress' && (
              <Button
                variant="ghost"
                size="icon"
                aria-label="Marquer en cours"
                title="Marquer en cours"
                onClick={() => onStatusChange('in_progress')}
              >
                <Clock className="h-[18px] w-[18px]" />
              </Button>
            )}
            {task.status !== 'done' && (
              <Button
                variant="ghost"
                size="icon"
                aria-label="Marquer terminé"
                title="Marquer terminé"
                onClick={() => onStatusChange('done')}
              >
                <CheckCircle2 className="h-[18px] w-[18px]" />
              </Button>
            )}
            {task.status === 'done' && (
              <Button
                variant="ghost"
                size="icon"
                aria-label="Rouvrir"
                title="Rouvrir"
                onClick={() => onStatusChange('todo')}
              >
                <Circle className="h-[18px] w-[18px]" />
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
