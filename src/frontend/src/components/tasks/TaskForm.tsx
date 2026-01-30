/**
 * THÉRÈSE v2 - Task Form
 *
 * Formulaire pour créer ou éditer une tâche.
 * Phase 3 - Tasks/Todos
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Save, Loader2 } from 'lucide-react';
import { useTaskStore } from '../../stores/taskStore';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

export function TaskForm() {
  const {
    tasks,
    currentTaskId,
    setIsTaskFormOpen,
    setCurrentTask,
    addTask,
    updateTask: updateTaskInStore,
    clearDraft,
  } = useTaskStore();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('todo');
  const [priority, setPriority] = useState('medium');
  const [dueDate, setDueDate] = useState('');
  const [projectId, setProjectId] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditing = !!currentTaskId;
  const task = tasks.find((t) => t.id === currentTaskId);

  // Load task data for editing
  useEffect(() => {
    if (isEditing && task) {
      setTitle(task.title);
      setDescription(task.description || '');
      setStatus(task.status);
      setPriority(task.priority);
      setDueDate(task.due_date ? task.due_date.split('T')[0] : '');
      setProjectId(task.project_id || '');
      setTagsInput(task.tags ? task.tags.join(', ') : '');
    }
  }, [isEditing, task]);

  async function handleSave() {
    if (!title.trim()) {
      setError('Veuillez ajouter un titre');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const tags = tagsInput
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t);

      if (isEditing && task) {
        // Update existing task
        const request: api.UpdateTaskRequest = {
          title,
          description: description || undefined,
          status,
          priority,
          due_date: dueDate ? `${dueDate}T00:00:00Z` : undefined,
          project_id: projectId || undefined,
          tags: tags.length > 0 ? tags : undefined,
        };

        const updated = await api.updateTask(task.id, request);
        updateTaskInStore(task.id, updated);
      } else {
        // Create new task
        const request: api.CreateTaskRequest = {
          title,
          description: description || undefined,
          status,
          priority,
          due_date: dueDate ? `${dueDate}T00:00:00Z` : undefined,
          project_id: projectId || undefined,
          tags: tags.length > 0 ? tags : undefined,
        };

        const created = await api.createTask(request);
        addTask(created);
      }

      clearDraft();
      setIsTaskFormOpen(false);
      setCurrentTask(null);
    } catch (err) {
      console.error('Failed to save task:', err);
      setError(err instanceof Error ? err.message : 'Échec de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    if (confirm('Abandonner les modifications ?')) {
      clearDraft();
      setIsTaskFormOpen(false);
      setCurrentTask(null);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="h-full flex flex-col"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={handleCancel}
            className="p-2 hover:bg-border/30 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-text-muted" />
          </button>
          <h3 className="text-lg font-semibold text-text">
            {isEditing ? 'Modifier la tâche' : 'Nouvelle tâche'}
          </h3>
        </div>

        <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Enregistrement...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Enregistrer
            </>
          )}
        </Button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {error && (
          <div className="px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Title */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Titre *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Titre de la tâche"
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>

        {/* Description */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description de la tâche"
            rows={4}
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 resize-none focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>

        {/* Status & Priority */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-text-muted mb-2 block">Statut</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            >
              <option value="todo">À faire</option>
              <option value="in_progress">En cours</option>
              <option value="done">Terminé</option>
              <option value="cancelled">Annulé</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-text-muted mb-2 block">Priorité</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            >
              <option value="low">Basse</option>
              <option value="medium">Moyenne</option>
              <option value="high">Haute</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
        </div>

        {/* Due Date */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Date limite</label>
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>

        {/* Tags */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Tags</label>
          <input
            type="text"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="design, urgent, client"
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
          <p className="text-xs text-text-muted mt-1">Séparez les tags par des virgules</p>
        </div>

        {/* Project (optional, future feature) */}
        {/* <div>
          <label className="text-sm text-text-muted mb-2 block">Projet lié</label>
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          >
            <option value="">Aucun</option>
            // Map projects here
          </select>
        </div> */}
      </div>
    </motion.div>
  );
}
