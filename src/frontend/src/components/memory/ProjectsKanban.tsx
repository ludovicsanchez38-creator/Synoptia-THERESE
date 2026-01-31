/**
 * THERESE v2 - Projects Kanban (vertical)
 *
 * Vue Kanban verticale pour les projets dans la sidebar droite (420px).
 * Sections empilees par statut avec drag & drop via @dnd-kit.
 */

import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Circle, Clock, CheckCircle2, XCircle,
  GripVertical, Trash2, Briefcase, ChevronRight,
} from 'lucide-react';
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

// =============================================================================
// CONSTANTES
// =============================================================================

const STATUS_COLUMNS = [
  { id: 'active', label: 'Actif', icon: Circle, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
  { id: 'on_hold', label: 'En attente', icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  { id: 'completed', label: 'Termine', icon: CheckCircle2, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  { id: 'cancelled', label: 'Annule', icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
] as const;

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

    if (COLUMN_IDS.includes(over.id as typeof COLUMN_IDS[number])) {
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
    return (
      <div className="flex flex-col items-center justify-center h-32 text-text-muted">
        <Briefcase className="w-8 h-8 mb-2 opacity-50" />
        <p className="text-sm">Aucun projet</p>
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="divide-y divide-border/30">
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
      className={`transition-colors ${isOver ? 'bg-accent-cyan/5' : ''}`}
    >
      {/* Section Header */}
      <div className={`flex items-center gap-2 px-3 py-2 ${column.bg}`}>
        <column.icon className={`w-4 h-4 ${column.color} ${column.id === 'active' ? 'fill-current' : ''}`} />
        <span className={`text-xs font-semibold uppercase tracking-wider ${column.color}`}>
          {column.label}
        </span>
        <span className="ml-auto text-xs text-text-muted">({projects.length})</span>
      </div>

      {/* Project Cards */}
      <SortableContext
        items={projects.map((p) => p.id)}
        strategy={verticalListSortingStrategy}
      >
        {projects.length === 0 ? (
          <div className={`flex items-center justify-center h-12 text-xs text-text-muted/50 transition-colors ${
            isOver ? 'bg-accent-cyan/10 text-accent-cyan/70' : ''
          }`}>
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
    transform,
    transition,
    isDragging,
  } = useSortable({ id: project.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <ProjectCard
        project={project}
        onSelect={onSelect}
        onDelete={onDelete}
        dragListeners={listeners}
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
  dragListeners?: Record<string, unknown>;
}

function ProjectCard({ project, onSelect, onDelete, isOverlay, dragListeners }: ProjectCardProps) {
  return (
    <motion.div
      whileHover={isOverlay ? undefined : { scale: 1.01 }}
      whileTap={isOverlay ? undefined : { scale: 0.99 }}
      className={`mx-2 my-1 px-3 py-2 rounded-lg border border-border/30 bg-surface/60 hover:bg-surface transition-colors group ${
        isOverlay ? 'shadow-xl ring-2 ring-accent-cyan/30 bg-surface' : ''
      }`}
    >
      <div className="flex items-center gap-2">
        {/* Drag Handle */}
        {dragListeners && (
          <div
            className="cursor-grab active:cursor-grabbing text-text-muted/30 hover:text-text-muted flex-shrink-0"
            {...dragListeners}
            onClick={(e) => e.stopPropagation()}
          >
            <GripVertical className="w-4 h-4" />
          </div>
        )}

        {/* Clickable area */}
        <button
          onClick={() => onSelect(project)}
          className="flex-1 min-w-0 text-left"
        >
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-text truncate">{project.name}</p>
            {project.budget != null && project.budget > 0 && (
              <span className="text-xs text-text-muted flex-shrink-0">
                {formatCurrency(project.budget)}
              </span>
            )}
          </div>
          {project.description && (
            <p className="text-xs text-text-muted truncate mt-0.5">{project.description}</p>
          )}
        </button>

        {/* Actions (hover) */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(project); }}
            className="p-1 rounded-md hover:bg-red-500/20 text-text-muted hover:text-red-400 transition-colors"
            title="Supprimer"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
        </div>
      </div>
    </motion.div>
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
