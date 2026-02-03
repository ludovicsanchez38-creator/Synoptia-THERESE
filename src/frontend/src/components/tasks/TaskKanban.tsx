/**
 * THÉRÈSE v2 - Task Kanban View
 *
 * Vue Kanban avec colonnes Todo/In Progress/Done.
 * Drag & Drop via @dnd-kit.
 * Phase 3 - Tasks/Todos
 */

import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Clock, AlertCircle, GripVertical } from 'lucide-react';
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

const COLUMNS = [
  { id: 'todo', label: 'A faire', icon: Circle, color: 'text-text-muted' },
  { id: 'in_progress', label: 'En cours', icon: Clock, color: 'text-blue-400' },
  { id: 'done', label: 'Termine', icon: CheckCircle2, color: 'text-green-400' },
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

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="h-full flex gap-4 p-6 overflow-x-auto">
        {COLUMNS.map((column) => (
          <DroppableColumn key={column.id} column={column} count={tasksByStatus[column.id].length}>
            <SortableContext
              items={tasksByStatus[column.id].map((t) => t.id)}
              strategy={verticalListSortingStrategy}
            >
              {tasksByStatus[column.id].length === 0 ? (
                <div className="flex items-center justify-center h-32">
                  <p className="text-sm text-text-muted">Aucune tache</p>
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
      className={`flex-1 min-w-[300px] flex flex-col bg-background/20 rounded-lg transition-colors ${
        isOver ? 'ring-2 ring-accent-cyan/50 bg-accent-cyan/5' : ''
      }`}
    >
      {/* Column Header */}
      <div className="px-4 py-3 border-b border-border/30 flex items-center gap-2">
        <column.icon className={`w-5 h-5 ${column.color}`} />
        <h3 className="text-sm font-medium text-text">{column.label}</h3>
        <span className="ml-auto text-xs text-text-muted">{count}</span>
      </div>

      {/* Tasks */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">{children}</div>
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
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <TaskCard
        task={task}
        onClick={onClick}
        onStatusChange={onStatusChange}
        dragListeners={listeners}
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
  dragListeners?: Record<string, unknown>;
  maskTextFn?: (text: string) => string;
}

function TaskCard({ task, onClick, onStatusChange, isOverlay, dragListeners, maskTextFn }: TaskCardProps) {
  const [showActions, setShowActions] = useState(false);

  const priorityColors = {
    urgent: 'bg-red-500/10 text-red-400 border-red-500/20',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    medium: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    low: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  };

  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';

  return (
    <motion.div
      whileHover={isOverlay ? undefined : { scale: 1.02 }}
      whileTap={isOverlay ? undefined : { scale: 0.98 }}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      className={`p-3 bg-surface-elevated/60 hover:bg-surface-elevated rounded-lg border border-border/30 cursor-pointer transition-colors relative ${
        isOverlay ? 'shadow-xl ring-2 ring-accent-cyan/30' : ''
      }`}
      onClick={onClick}
    >
      {/* Drag Handle */}
      {dragListeners && (
        <div
          className="absolute top-3 left-1 cursor-grab active:cursor-grabbing text-text-muted/40 hover:text-text-muted"
          {...dragListeners}
          onClick={(e) => e.stopPropagation()}
        >
          <GripVertical className="w-4 h-4" />
        </div>
      )}

      <div className={dragListeners ? 'pl-5' : ''}>
        {/* Priority Badge */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`px-2 py-0.5 text-xs rounded border ${
              priorityColors[task.priority as keyof typeof priorityColors]
            }`}
          >
            {task.priority === 'urgent' && 'Urgent'}
            {task.priority === 'high' && 'Haute'}
            {task.priority === 'medium' && 'Moyenne'}
            {task.priority === 'low' && 'Basse'}
          </span>
          {isOverdue && (
            <span className="flex items-center gap-1 text-xs text-red-400">
              <AlertCircle className="w-3 h-3" />
              En retard
            </span>
          )}
        </div>

        {/* Title */}
        <h4 className="text-sm font-medium text-text mb-1">{maskTextFn ? maskTextFn(task.title) : task.title}</h4>

        {/* Description */}
        {task.description && (
          <p className="text-xs text-text-muted line-clamp-2 mb-2">{maskTextFn ? maskTextFn(task.description) : task.description}</p>
        )}

        {/* Due Date */}
        {task.due_date && (
          <p className="text-xs text-text-muted">
            {new Date(task.due_date).toLocaleDateString('fr-FR', {
              day: 'numeric',
              month: 'short',
            })}
          </p>
        )}

        {/* Tags */}
        {task.tags && task.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {task.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 text-xs bg-accent-cyan/10 text-accent-cyan rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions (on hover) */}
      {showActions && !isOverlay && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-2 right-2 flex items-center gap-1 bg-surface/90 backdrop-blur-sm rounded-lg p-1 border border-border/50"
          onClick={(e) => e.stopPropagation()}
        >
          {task.status !== 'in_progress' && (
            <button
              onClick={() => onStatusChange('in_progress')}
              className="p-1 hover:bg-blue-500/20 rounded transition-colors"
              title="Marquer en cours"
            >
              <Clock className="w-3 h-3 text-blue-400" />
            </button>
          )}
          {task.status !== 'done' && (
            <button
              onClick={() => onStatusChange('done')}
              className="p-1 hover:bg-green-500/20 rounded transition-colors"
              title="Marquer termine"
            >
              <CheckCircle2 className="w-3 h-3 text-green-400" />
            </button>
          )}
          {task.status === 'done' && (
            <button
              onClick={() => onStatusChange('todo')}
              className="p-1 hover:bg-gray-500/20 rounded transition-colors"
              title="Rouvrir"
            >
              <Circle className="w-3 h-3 text-text-muted" />
            </button>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
