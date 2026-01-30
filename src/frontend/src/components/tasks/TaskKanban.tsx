/**
 * THÉRÈSE v2 - Task Kanban View
 *
 * Vue Kanban avec colonnes Todo/In Progress/Done.
 * Phase 3 - Tasks/Todos
 */

import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Clock, X, AlertCircle } from 'lucide-react';
import { useTaskStore } from '../../stores/taskStore';
import type { Task } from '../../services/api';
import * as api from '../../services/api';

const COLUMNS = [
  { id: 'todo', label: 'À faire', icon: Circle, color: 'text-text-muted' },
  { id: 'in_progress', label: 'En cours', icon: Clock, color: 'text-blue-400' },
  { id: 'done', label: 'Terminé', icon: CheckCircle2, color: 'text-green-400' },
];

export function TaskKanban() {
  const { tasks, searchQuery, setCurrentTask, setIsTaskFormOpen, updateTask } = useTaskStore();

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

  return (
    <div className="h-full flex gap-4 p-6 overflow-x-auto">
      {COLUMNS.map((column) => (
        <div
          key={column.id}
          className="flex-1 min-w-[300px] flex flex-col bg-background/20 rounded-lg"
        >
          {/* Column Header */}
          <div className="px-4 py-3 border-b border-border/30 flex items-center gap-2">
            <column.icon className={`w-5 h-5 ${column.color}`} />
            <h3 className="text-sm font-medium text-text">{column.label}</h3>
            <span className="ml-auto text-xs text-text-muted">
              {tasksByStatus[column.id].length}
            </span>
          </div>

          {/* Tasks */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {tasksByStatus[column.id].length === 0 ? (
              <div className="flex items-center justify-center h-32">
                <p className="text-sm text-text-muted">Aucune tâche</p>
              </div>
            ) : (
              tasksByStatus[column.id].map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onClick={() => handleTaskClick(task.id)}
                  onStatusChange={(newStatus) => handleStatusChange(task.id, newStatus)}
                />
              ))
            )}
          </div>
        </div>
      ))}
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
}

function TaskCard({ task, onClick, onStatusChange }: TaskCardProps) {
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
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      className="p-3 bg-surface-elevated/60 hover:bg-surface-elevated rounded-lg border border-border/30 cursor-pointer transition-colors relative"
      onClick={onClick}
    >
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
      <h4 className="text-sm font-medium text-text mb-1">{task.title}</h4>

      {/* Description */}
      {task.description && (
        <p className="text-xs text-text-muted line-clamp-2 mb-2">{task.description}</p>
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

      {/* Quick Actions (on hover) */}
      {showActions && (
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
              title="Marquer terminé"
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
