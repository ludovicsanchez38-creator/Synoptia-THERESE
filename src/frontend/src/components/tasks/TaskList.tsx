/**
 * THÉRÈSE v2 - Task List View
 *
 * Vue liste des tâches.
 * Phase 3 - Tasks/Todos
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Clock, AlertCircle, Trash2 } from 'lucide-react';
import { useTaskStore } from '../../stores/taskStore';
import type { Task } from '../../services/api';
import * as api from '../../services/api';
import { useDemoMask } from '../../hooks';
import { Button } from '../ui/Button';

export function TaskList() {
  const { tasks, searchQuery, setCurrentTask, setIsTaskFormOpen, updateTask, removeTask } =
    useTaskStore();
  const { maskText } = useDemoMask();

  // Filter tasks
  const filteredTasks = useMemo(() => {
    if (!searchQuery) return tasks;

    const query = searchQuery.toLowerCase();
    return tasks.filter(
      (t) =>
        t.title.toLowerCase().includes(query) || t.description?.toLowerCase().includes(query)
    );
  }, [tasks, searchQuery]);

  async function handleToggleComplete(task: Task, e: React.MouseEvent) {
    e.stopPropagation();

    try {
      if (task.status === 'done') {
        const updated = await api.uncompleteTask(task.id);
        updateTask(task.id, updated);
      } else {
        const updated = await api.completeTask(task.id);
        updateTask(task.id, updated);
      }
    } catch (err) {
      console.error('Failed to toggle task:', err);
    }
  }

  async function handleDelete(taskId: string, e: React.MouseEvent) {
    e.stopPropagation();

    if (!confirm('Supprimer cette tâche ?')) return;

    try {
      await api.deleteTask(taskId);
      removeTask(taskId);
    } catch (err) {
      console.error('Failed to delete task:', err);
    }
  }

  function handleTaskClick(taskId: string) {
    setCurrentTask(taskId);
    setIsTaskFormOpen(true);
  }

  const priorityColors = {
    urgent: 'text-error',
    high: 'text-orange-400',
    medium: 'text-blue-400',
    low: 'text-text-muted',
  };

  if (filteredTasks.length === 0) {
    /* Un écran vide est le moment où l'on a le PLUS besoin d'être guidé :
       c'est souvent la première fois qu'on l'ouvre. « Aucune tâche » seul au
       milieu constatait le vide sans proposer d'en sortir - le bouton de
       création existait, mais dans la barre du haut, loin du regard. */
    const filtre = searchQuery.trim();
    return (
      <div className="flex h-full items-center justify-center px-6">
        <div className="max-w-sm text-center">
          <CheckCircle2 className="mx-auto h-9 w-9 text-text-muted" />
          <p className="mt-3 text-base font-semibold text-text">
            {filtre ? 'Aucune tâche ne correspond' : 'Aucune tâche pour l’instant'}
          </p>
          <p className="mt-1 text-sm leading-5 text-text-muted">
            {filtre
              ? `Rien ne correspond à « ${filtre} ». Essaie un autre mot, ou crée cette tâche.`
              : 'Note ce que tu ne veux pas oublier : Thérèse le gardera avec le reste de ton contexte.'}
          </p>
          <Button
            variant="primary"
            size="sm"
            className="mt-4"
            onClick={() => {
              setCurrentTask(null);
              setIsTaskFormOpen(true);
            }}
          >
            Créer une tâche
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      <div className="space-y-2">
        {filteredTasks.map((task) => {
          const isOverdue =
            task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';
          const isDone = task.status === 'done';

          return (
            <motion.div
              key={task.id}
              whileHover={{ scale: 1.005 }}
              whileTap={{ scale: 0.995 }}
              onClick={() => handleTaskClick(task.id)}
              className={`p-4 bg-surface-elevated/60 hover:bg-surface-elevated rounded-md border border-border/30 cursor-pointer transition-colors ${
                isDone ? 'opacity-60' : ''
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Checkbox */}
                <button
                  onClick={(e) => handleToggleComplete(task, e)}
                  className="mt-0.5 shrink-0 hover:scale-110 transition-transform"
                >
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                  ) : (
                    <Circle className="w-5 h-5 text-text-muted" />
                  )}
                </button>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 mb-1">
                    <h4
                      className={`text-sm font-medium ${
                        isDone ? 'line-through text-text-muted' : 'text-text'
                      }`}
                    >
                      {maskText(task.title)}
                    </h4>

                    {/* Priority & Status */}
                    <div className="flex items-center gap-2 shrink-0">
                      {task.status === 'in_progress' && (
                        <Clock className="w-4 h-4 text-blue-400" />
                      )}
                      {isOverdue && <AlertCircle className="w-4 h-4 text-error" />}
                      <span
                        className={`text-xs font-medium ${
                          priorityColors[task.priority as keyof typeof priorityColors]
                        }`}
                      >
                        {task.priority === 'urgent' && 'Urgent'}
                        {task.priority === 'high' && 'Haute'}
                        {task.priority === 'medium' && 'Moyenne'}
                        {task.priority === 'low' && 'Basse'}
                      </span>
                    </div>
                  </div>

                  {/* Description */}
                  {task.description && (
                    <p className="text-xs text-text-muted line-clamp-1 mb-2">
                      {maskText(task.description)}
                    </p>
                  )}

                  {/* Footer */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      {/* Due Date */}
                      {task.due_date && (
                        <span
                          className={`text-xs ${
                            isOverdue ? 'text-error font-medium' : 'text-text-muted'
                          }`}
                        >
                          {new Date(task.due_date).toLocaleDateString('fr-FR', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </span>
                      )}

                      {/* Tags */}
                      {task.tags && task.tags.length > 0 && (
                        <div className="flex gap-1">
                          {task.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-0.5 text-xs bg-accent-cyan/10 text-accent-cyan-ink rounded-sm"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Delete Button */}
                    <button
                      onClick={(e) => handleDelete(task.id, e)}
                      className="p-1 hover:bg-error/20 rounded-sm transition-colors"
                      title="Supprimer"
                    >
                      <Trash2 className="w-4 h-4 text-text-muted hover:text-error" />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
