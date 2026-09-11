/**
 * THERESE v2 - Projects Kanban (vertical)
 *
 * Vue Kanban verticale pour les projets dans la sidebar droite (420px).
 * Sections empilees par statut avec drag & drop via @dnd-kit.
 *
 * DA « Application affinée », lot 6 (11/09/2026) : les quatre têtes sont des
 * `Etiquette` avec un compte nu ; la couleur du groupe passe par l'étiquette,
 * plus par un fond d'agent.
 */

import { useMemo, useState } from 'react';
import { GripVertical, Trash2, ChevronRight } from 'lucide-react';
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
import type { Project } from '../../services/api';
import { accessibiliteGlisserDeposer } from '../../lib/accessibiliteGlisserDeposer';
import { Button } from '../ui/Button';
import { EtatVide } from '../ui/EtatVide';
import { Etiquette, type TonEtiquette } from '../ui/Etiquette';
import { cn } from '../../lib/utils';

// =============================================================================
// CONSTANTES
// =============================================================================

const STATUS_COLUMNS: { id: string; label: string; ton: TonEtiquette }[] = [
  { id: 'active', label: 'Actif', ton: 'succes' },
  { id: 'on_hold', label: 'En attente', ton: 'attention' },
  { id: 'completed', label: 'Terminé', ton: 'info' },
  { id: 'cancelled', label: 'Annulé', ton: 'erreur' },
];

const COLUMN_IDS = STATUS_COLUMNS.map((c) => c.id);

/** Normalise les statuts backend : 'pending' -> 'on_hold' */
function normalizeStatus(status: string): string {
  if (status === 'pending') return 'on_hold';
  return status;
}

// =============================================================================
// PROPS
// =============================================================================

interface ProjectsKanbanProps {
  projects: Project[];
  onSelect: (project: Project) => void;
  onDelete: (project: Project) => void;
  onStatusChange: (projectId: string, newStatus: string) => Promise<void>;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function ProjectsKanban({ projects, onSelect, onDelete, onStatusChange }: ProjectsKanbanProps) {
  const [activeProject, setActiveProject] = useState<Project | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor)
  );

  // Group projects by normalized status
  const projectsByStatus = useMemo(() => {
    const groups: Record<string, Project[]> = {};
    for (const col of STATUS_COLUMNS) {
      groups[col.id] = [];
    }

    for (const project of projects) {
      const status = normalizeStatus(project.status);
      if (groups[status]) {
        groups[status].push(project);
      } else {
        // Statut inconnu -> actif par defaut
        groups['active'].push(project);
      }
    }

    return groups;
  }, [projects]);

  function handleDragStart(event: DragStartEvent) {
    const projectId = event.active.id as string;
    const project = projects.find((p) => p.id === projectId);
    if (project) setActiveProject(project);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveProject(null);

    const { active, over } = event;
    if (!over) return;

    const projectId = active.id as string;

    // Determine target column
    let targetColumn: string | null = null;

    if (COLUMN_IDS.includes(over.id as string)) {
      targetColumn = over.id as string;
    } else {
      // Dropped on a project card - find its column
      for (const colId of COLUMN_IDS) {
        if (projectsByStatus[colId]?.some((p) => p.id === over.id)) {
          targetColumn = colId;
          break;
        }
      }
    }

    if (!targetColumn) return;

    const currentProject = projects.find((p) => p.id === projectId);
    if (!currentProject) return;

    const currentStatus = normalizeStatus(currentProject.status);
    if (currentStatus === targetColumn) return;

    onStatusChange(projectId, targetColumn);
  }

  if (projects.length === 0) {
    // Filet : l'état vide de l'utilisateur vit dans le panneau, qui ne monte
    // même pas ce kanban. Ici, c'est le montage isolé (tests, réemploi).
    return <EtatVide titre="Aucun projet" />;
  }

  // B-217 : consignes et annonces en français, par les noms - un projet
  // annoncé par son UUID ne désigne rien à l'oreille.
  const accessibilite = accessibiliteGlisserDeposer((id) =>
    projects.find((project) => project.id === id)?.name
      ?? STATUS_COLUMNS.find((column) => column.id === id)?.label
      ?? null,
  );

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setActiveProject(null)}
      accessibility={accessibilite}
    >
      <div className="divide-y divide-border">
        {STATUS_COLUMNS.map((column) => (
          <DroppableStatusGroup
            key={column.id}
            column={column}
            projects={projectsByStatus[column.id]}
            onSelect={onSelect}
            onDelete={onDelete}
          />
        ))}
      </div>

      <DragOverlay>
        {activeProject && (
          <ProjectCard
            project={activeProject}
            onSelect={() => {}}
            onDelete={() => {}}
            isOverlay
            showDragHandle
          />
        )}
      </DragOverlay>
    </DndContext>
  );
}

// =============================================================================
// DROPPABLE STATUS GROUP
// =============================================================================

interface DroppableStatusGroupProps {
  column: (typeof STATUS_COLUMNS)[number];
  projects: Project[];
  onSelect: (project: Project) => void;
  onDelete: (project: Project) => void;
}

function DroppableStatusGroup({ column, projects, onSelect, onDelete }: DroppableStatusGroupProps) {
  const { isOver, setNodeRef } = useDroppable({ id: column.id });

  return (
    <div
      ref={setNodeRef}
      className={cn('transition-colors', isOver && 'bg-accent-tint')}
    >
      {/* Section Header. P-046 (Karim, c4) : même casse que le kanban des
          tâches (casse de phrase du lexique), plus de capitales. Même POLICE
          et même GRAISSE aussi : la tête jumelle est un `h3`, à qui le socle
          donne la display et `letter-spacing: -0.01em` (`globals.css:607-611`)
          ; ce `div` les prend explicitement. Compte à 500, comme la maquette
          (`.col h3 .compte{font-weight:500}`, `projets.html:12`). */}
      <div className="flex items-center gap-2 px-3 py-2 text-sm font-editorial tracking-[-0.01em]">
        <Etiquette ton={column.ton}>{column.label}</Etiquette>
        <span className="ml-auto text-sm font-medium tabular-nums text-text-muted">{projects.length}</span>
      </div>

      {/* Project Cards */}
      <SortableContext
        items={projects.map((p) => p.id)}
        strategy={verticalListSortingStrategy}
      >
        {projects.length === 0 ? (
          <div className={cn(
            'flex items-center justify-center h-12 text-sm text-text-muted transition-colors',
            isOver && 'bg-accent-tint text-accent-cyan-ink',
          )}>
            Glisser ici
          </div>
        ) : (
          <div className="py-1">
            {projects.map((project) => (
              <SortableProjectCard
                key={project.id}
                project={project}
                onSelect={onSelect}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </SortableContext>
    </div>
  );
}

// =============================================================================
// SORTABLE PROJECT CARD
// =============================================================================

interface SortableProjectCardProps {
  project: Project;
  onSelect: (project: Project) => void;
  onDelete: (project: Project) => void;
}

function SortableProjectCard({ project, onSelect, onDelete }: SortableProjectCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: project.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  // BUG-041 : les listeners couvrent toute la carte (même idiome que le
  // PipelineView CRM), pas seulement la poignée - sinon attraper la carte
  // par son corps ne démarre aucun drag. Les clics simples (ouvrir,
  // supprimer) restent distingués du drag par l'activationConstraint
  // (distance 8px) du PointerSensor.
  // B-750 : même défaut que le kanban des tâches. Tant que
  // `setActivatorNodeRef` n'est pas appelé, la garde du KeyboardSensor
  // (`event.target !== activator`) ne s'applique pas et le capteur saisit la
  // carte sur un Entrée parti du bouton du nom ou de la corbeille. L'enveloppe
  // est le nœud activateur : elle porte déjà les écouteurs et le focus.
  return (
    <div
      ref={(noeud) => { setNodeRef(noeud); setActivatorNodeRef(noeud); }}
      style={style}
      className="cursor-grab active:cursor-grabbing"
      {...attributes}
      {...listeners}
    >
      <ProjectCard
        project={project}
        onSelect={onSelect}
        onDelete={onDelete}
        showDragHandle
      />
    </div>
  );
}

// =============================================================================
// PROJECT CARD
// =============================================================================

interface ProjectCardProps {
  project: Project;
  onSelect: (project: Project) => void;
  onDelete: (project: Project) => void;
  isOverlay?: boolean;
  showDragHandle?: boolean;
}

function ProjectCard({ project, onSelect, onDelete, isOverlay, showDragHandle }: ProjectCardProps) {
  return (
    <div
      // `group` porte la révélation de la corbeille : sans lui, elle reste à
      // opacité 0 au survol comme au focus. Pas de `transition-colors` : la
      // carte n'a plus aucune couleur qui change (la maquette ne pose pas de
      // `:hover` sur une carte) ; le retour au survol, c'est la corbeille qui
      // apparaît, et elle a sa propre `transition-opacity`.
      className={cn(
        'mx-2 my-1 px-3 py-2 rounded-sm border border-border bg-surface group',
        isOverlay && 'shadow-lg ring-2 ring-ring/30',
      )}
    >
      <div className="flex items-center gap-2">
        {/* Poignée (repère visuel : toute la carte est draggable) */}
        {showDragHandle && (
          <div className="text-text-muted flex-shrink-0">
            <GripVertical className="w-4 h-4" />
          </div>
        )}

        {/* Clickable area */}
        <button
          onClick={() => onSelect(project)}
          className="flex-1 min-w-0 min-h-9 text-left"
        >
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-text truncate">{project.name}</p>
            {project.budget != null && project.budget > 0 && (
              <span className="text-xs text-text-muted flex-shrink-0">
                {formatCurrency(project.budget)}
              </span>
            )}
          </div>
          {project.description && (
            <p className="text-sm text-text-muted truncate mt-0.5">{project.description}</p>
          )}
        </button>

        {/* Actions (hover). `group-focus-within` va toujours de pair avec
            `group-hover` : au clavier, le focus se poserait sinon sur un
            bouton invisible (E1). */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity flex-shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => { e.stopPropagation(); onDelete(project); }}
            aria-label={`Supprimer ${project.name}`}
            title="Supprimer"
          >
            <Trash2 className="h-[18px] w-[18px]" />
          </Button>
          <ChevronRight aria-hidden="true" className="w-3.5 h-3.5 text-text-muted" />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// HELPERS
// =============================================================================

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(amount);
}
