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

import { useId, useMemo, useState } from 'react';
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
import { useDemoMask } from '../../hooks';
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
  const { maskText } = useDemoMask();
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
  const accessibilite = accessibiliteGlisserDeposer((id) => {
    const project = projects.find((item) => item.id === id);
    if (project) return maskText(project.name);
    return STATUS_COLUMNS.find((column) => column.id === id)?.label ?? null;
  });

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
  const { maskText: masquer } = useDemoMask();
  const nomAccessible = masquer(project.name) || 'Projet';

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  // Le pointeur saisit la carte entière ; le clavier utilise une poignée
  // distincte du nom et de la suppression, sans boutons imbriqués.
  return (
    <div
      ref={setNodeRef}
      style={style}
      className="cursor-grab active:cursor-grabbing"
      onPointerDown={(event) => listeners?.onPointerDown?.(event)}
    >
      <ProjectCard
        project={project}
        onSelect={onSelect}
        onDelete={onDelete}
        isDragging={isDragging}
        showDragHandle
        poignee={(tabIndex) => <button type="button" ref={setActivatorNodeRef} {...attributes} {...listeners}
          tabIndex={tabIndex}
          aria-label={`Déplacer ${nomAccessible}`}
          className="text-text-muted flex-shrink-0 cursor-grab active:cursor-grabbing">
          <GripVertical className="w-4 h-4" aria-hidden />
        </button>}
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
  isDragging?: boolean;
  showDragHandle?: boolean;
  poignee?: (tabIndex: number) => React.ReactNode;
}

function ProjectCard({ project, onSelect, onDelete, isOverlay, isDragging, showDragHandle, poignee }: ProjectCardProps) {
  // B-752 : le masque du mode démo s'arrêtait aux tâches et aux contacts. Les
  // projets arrivent BRUTS du panneau, et cette carte est le seul endroit où
  // leur nom est rendu - ici pour les cartes de la liste comme pour celle du
  // `DragOverlay`. Le nom accessible de la corbeille passe par le masque au
  // même titre que le texte visible : un nom masqué à l'œil et nu à l'oreille
  // ne masque rien (même reprise que `TaskList`, D105 et D106).
  const { maskText } = useDemoMask();
  const nom = maskText(project.name);
  const aideId = useId();
  // P-107 : ordre poignée, nom, corbeille ; le nom est l'arrêt initial.
  const [commandeActive, setCommandeActive] = useState(1);

  return (
    <div
      role="group"
      aria-label={nom || 'Projet'}
      aria-describedby={aideId}
      aria-hidden={isOverlay || undefined}
      onFocus={(event) => {
        if (!(event.target instanceof HTMLButtonElement)) return;
        const commandes = Array.from(event.currentTarget.querySelectorAll('button'));
        const index = commandes.indexOf(event.target);
        if (index !== -1) setCommandeActive(index);
      }}
      onKeyDown={(event) => {
        // Pendant un glisser, dnd-kit garde les flèches pour déplacer la carte.
        // Tab et les touches d'activation conservent leur comportement natif.
        if (isDragging || isOverlay || (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight')) return;
        if (!(event.target instanceof HTMLButtonElement)) return;
        const commandes = Array.from(event.currentTarget.querySelectorAll('button'));
        const index = commandes.indexOf(event.target);
        if (index === -1) return;
        event.preventDefault();
        event.stopPropagation();
        // Sans boucle : une flèche vers l'extérieur reste sur le bouton de bord.
        const suivant = Math.max(0, Math.min(commandes.length - 1, index + (event.key === 'ArrowRight' ? 1 : -1)));
        commandes[suivant].focus();
      }}
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
      <span id={aideId} className="sr-only">
        Flèches gauche et droite : choisir entre déplacer, ouvrir ou supprimer le projet.
      </span>
      <div className="flex items-center gap-2">
        {/* Poignée (repère visuel : toute la carte est draggable) */}
        {poignee?.(!isOverlay && commandeActive === 0 ? 0 : -1) ?? (showDragHandle && (
          <div className="text-text-muted flex-shrink-0">
            <GripVertical className="w-4 h-4" />
          </div>
        ))}

        {/* Clickable area */}
        <button
          tabIndex={!isOverlay && commandeActive === 1 ? 0 : -1}
          onClick={() => onSelect(project)}
          className="flex-1 min-w-0 min-h-9 text-left"
        >
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-text truncate">{nom}</p>
            {project.budget != null && project.budget > 0 && (
              <span className="text-xs text-text-muted flex-shrink-0">
                {formatCurrency(project.budget)}
              </span>
            )}
          </div>
          {project.description && (
            <p className="text-sm text-text-muted truncate mt-0.5">{maskText(project.description)}</p>
          )}
          {/* P-123 : les tags saisis n'apparaissaient nulle part. */}
          {project.tags && project.tags.length > 0 && (
            <span className="mt-1 flex flex-wrap gap-1">
              {project.tags.map((tag) => (
                <Etiquette key={tag}>{maskText(tag)}</Etiquette>
              ))}
            </span>
          )}
        </button>

        {/* Actions (hover). `group-focus-within` va toujours de pair avec
            `group-hover` : au clavier, le focus se poserait sinon sur un
            bouton invisible (E1). */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity flex-shrink-0">
          <Button
            variant="ghost"
            size="icon"
            tabIndex={!isOverlay && commandeActive === 2 ? 0 : -1}
            onClick={(e) => { e.stopPropagation(); onDelete(project); }}
            aria-label={`Supprimer ${nom}`}
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
