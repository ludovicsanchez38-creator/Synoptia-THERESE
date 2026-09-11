/**
 * THÉRÈSE v2 - Task List View
 *
 * Vue liste des tâches.
 * Phase 3 - Tasks/Todos
 *
 * DA « Application affinée », lot 6 (11/09/2026) : rangées en grille
 * `2.25rem 1fr auto`, même barre de priorité que les colonnes, état vide sur
 * `EtatVide`. `Ligne` n'est pas montée : sa puce cliquable et sa corbeille
 * seraient recouvertes par le `before:inset-0` de son titre.
 */

import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Circle, Clock, AlertCircle, Trash2 } from 'lucide-react';
import { useTaskStore } from '../../stores/taskStore';
import type { Task } from '../../services/api';
import * as api from '../../services/api';
import { useDemoMask } from '../../hooks';
import { Button } from '../ui/Button';
import { Etiquette } from '../ui/Etiquette';
import { EtatVide } from '../ui/EtatVide';
import { cn } from '../../lib/utils';
import { isPastParisCivilDate } from '../../lib/civilDate';
import { useStatusStore } from '../../stores/statusStore';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { CLASSE_BARRE_PRIORITE, barrePriorite } from './prioriteBarre';

export function TaskList() {
  const { tasks, searchQuery, setCurrentTask, setIsTaskFormOpen, updateTask, removeTask } =
    useTaskStore();
  const { maskText } = useDemoMask();
  // D106 : plus de confirm() natif ; confirmation en ligne dans la carte,
  // fail-closed, et Échap ne ferme que la question.
  const [tacheASupprimer, setTacheASupprimer] = useState<Task | null>(null);
  useEffect(() => {
    if (!tacheASupprimer) return;
    return pushEscapeHandler(() => setTacheASupprimer(null));
  }, [tacheASupprimer]);

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
      useStatusStore.getState().addNotification({ type: 'error', title: 'Tâche non mise à jour', message: 'Le changement n’a pas été enregistré. Réessaie dans un instant.' });
    }
  }

  function handleDelete(task: Task, e: React.MouseEvent) {
    e.stopPropagation();
    setTacheASupprimer(task);
  }

  async function confirmerLaSuppression() {
    const cible = tacheASupprimer;
    if (!cible) return;
    setTacheASupprimer(null);
    try {
      await api.deleteTask(cible.id);
      removeTask(cible.id);
    } catch (err) {
      console.error('Failed to delete task:', err);
      useStatusStore.getState().addNotification({ type: 'error', title: 'Tâche non supprimée', message: 'La suppression n’a pas été enregistrée. Réessaie dans un instant.' });
    }
  }

  function handleTaskClick(taskId: string) {
    setCurrentTask(taskId);
    setIsTaskFormOpen(true);
  }

  if (filteredTasks.length === 0) {
    /* Un écran vide est le moment où l'on a le PLUS besoin d'être guidé :
       c'est souvent la première fois qu'on l'ouvre. « Aucune tâche » seul au
       milieu constatait le vide sans proposer d'en sortir - le bouton de
       création existait, mais dans la barre du haut, loin du regard. */
    const filtre = searchQuery.trim();
    return (
      <EtatVide
        className="h-full flex flex-col items-center justify-center"
        titre={filtre ? 'Aucune tâche ne correspond' : 'Aucune tâche pour l’instant'}
        action={(
          <Button
            variant="primary"
            size="md"
            onClick={() => {
              setCurrentTask(null);
              setIsTaskFormOpen(true);
            }}
          >
            Créer une tâche
          </Button>
        )}
      >
        {filtre
          ? `Rien ne correspond à « ${filtre} ». Essaie un autre mot, ou crée cette tâche.`
          : 'Note ce que tu ne veux pas oublier : Thérèse le gardera avec le reste de ton contexte.'}
      </EtatVide>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      {filteredTasks.map((task) => {
        const isOverdue = Boolean(
          task.due_date
            && isPastParisCivilDate(task.due_date)
            && !['done', 'cancelled'].includes(task.status),
        );
        const isDone = task.status === 'done';
        const barre = barrePriorite(task.priority);

        return (
          <div
            key={task.id}
            /* B-151 : repère par élément pour les protocoles (`qsa`). */
            data-testid="task-item"
            /* D105 : la rangée s'ouvre à la souris ; au clavier, c'est le titre
               qui porte l'action, avec un nom. Pas de rôle ni de tabIndex ici :
               deux arrêts de tabulation pour un même geste. */
            onClick={() => handleTaskClick(task.id)}
            className="grid grid-cols-[2.25rem_1fr_auto] gap-3 items-start px-4 py-3 border-t border-border hover:bg-surface-2 relative cursor-pointer transition-colors"
          >
            {/* Cocher */}
            <Button
              variant="ghost"
              size="icon"
              className="relative z-10"
              onClick={(e) => handleToggleComplete(task, e)}
              aria-label={task.status === 'done' ? `Rouvrir la tâche ${task.title}` : `Marquer la tâche ${task.title} terminée`}
            >
              {isDone ? (
                <CheckCircle2 className="h-[18px] w-[18px] text-success" />
              ) : (
                <Circle className="h-[18px] w-[18px] text-text-muted" />
              )}
            </Button>

            {/* Corps */}
            <div className="flex items-start gap-2 min-w-0">
              {barre && (
                <span role="img" aria-label={barre.nom} className={cn(CLASSE_BARRE_PRIORITE, barre.classe)} />
              )}

              <div className="min-w-0 flex-1">
                <div className="flex items-start gap-2">
                  <button
                    type="button"
                    aria-label={`Ouvrir la tâche ${task.title}`}
                    onClick={(e) => { e.stopPropagation(); handleTaskClick(task.id); }}
                    className={cn(
                      'relative z-10 font-semibold text-left',
                      isDone ? 'line-through text-text-muted' : 'text-text',
                    )}
                  >
                    {maskText(task.title)}
                  </button>
                  {task.status === 'in_progress' && (
                    <Clock aria-hidden="true" className="h-[18px] w-[18px] shrink-0 text-info" />
                  )}
                </div>

                {/* Description. B-134 : c'est le CORPS de la rangée, pas une
                    métadonnée. À 12 px comme la priorité et l'échéance,
                    l'écran n'avait plus de hiérarchie. */}
                {task.description && (
                  <p className="text-sm text-text-muted line-clamp-1">
                    {maskText(task.description)}
                  </p>
                )}
              </div>
            </div>

            {/* Droite */}
            <div className="flex items-center gap-2 relative z-10">
              {isOverdue && <Etiquette ton="erreur">En retard</Etiquette>}

              {task.due_date && (
                <span className="text-xs font-medium text-text-muted">
                  {new Date(task.due_date).toLocaleDateString('fr-FR', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
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

              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => handleDelete(task, e)}
                title="Supprimer"
                aria-label={`Supprimer la tâche ${task.title}`}
              >
                <Trash2 className="h-[18px] w-[18px]" />
              </Button>
            </div>

            {tacheASupprimer?.id === task.id && (
              /* Ce n'est pas une erreur : pas d'`Alerte`, donc pas de
                 `role="alert"` - la question est déjà sous les yeux. */
              <div
                className="col-span-3 flex items-center gap-2 rounded-sm border border-error/30 bg-[var(--color-error-tint)] px-3 py-3"
                onClick={(e) => e.stopPropagation()}
              >
                <AlertCircle aria-hidden="true" className="h-[18px] w-[18px] text-error shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-error">Supprimer « {maskText(task.title)} » ?</p>
                  <p className="text-xs text-error">Cette action est irréversible.</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="md" onClick={() => setTacheASupprimer(null)}>Conserver la tâche</Button>
                  <Button variant="danger" size="md" onClick={confirmerLaSuppression}>Supprimer définitivement</Button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
