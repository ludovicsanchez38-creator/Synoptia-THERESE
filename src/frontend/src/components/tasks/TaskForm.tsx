/**
 * THÉRÈSE v2 - Task Form
 *
 * Formulaire pour créer ou éditer une tâche.
 * Phase 3 - Tasks/Todos
 *
 * DA « Application affinée », lot 6 (11/09/2026) : les six champs passent par
 * `FormField` et les primitives ; le titre manquant devient une erreur DE
 * CHAMP (la `.erreur-champ` de la maquette), et non plus le bandeau réservé
 * aux échecs de sauvegarde.
 */

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, ChevronLeft, Save } from 'lucide-react';
import { useTaskStore } from '../../stores/taskStore';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import * as api from '../../services/api';
import { Spinner } from '../ui/Spinner';

/** Le message exact de la maquette (`projets.html:53`). */
const ERREUR_TITRE_MANQUANT = "Ajoute un titre : c'est la seule chose obligatoire.";

const OPTIONS_STATUT = [
  { value: 'todo', label: 'À faire' },
  { value: 'in_progress', label: 'En cours' },
  { value: 'done', label: 'Terminé' },
  { value: 'cancelled', label: 'Annulé' },
];

const OPTIONS_PRIORITE = [
  { value: 'low', label: 'Basse' },
  { value: 'medium', label: 'Moyenne' },
  { value: 'high', label: 'Haute' },
  { value: 'urgent', label: 'Urgent' },
];

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
  // Lot 6 : l'erreur du champ est un état DISTINCT du bandeau. Avec un seul
  // état, un échec de sauvegarde suivi d'un titre vidé laissait les deux
  // messages à l'écran, ou remplaçait l'un par l'autre au hasard de l'ordre.
  const [erreurTitre, setErreurTitre] = useState<string | null>(null);

  const isEditing = !!currentTaskId;
  const task = tasks.find((t) => t.id === currentTaskId);

  // Load task data for editing.
  // #189 : une fois par tâche ouverte, pas à chaque nouvelle instance de
  // l'objet (un rafraîchissement de la liste pendant la saisie réécrivait
  // les six champs avec les valeurs du serveur).
  const tacheChargeeRef = useRef<string | null>(null);
  useEffect(() => {
    if (isEditing && task && tacheChargeeRef.current !== task.id) {
      tacheChargeeRef.current = task.id;
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
      // Les deux ensemble : le bandeau d'un échec précédent tombe, le champ
      // porte seul la demande.
      setError(null);
      setErreurTitre(ERREUR_TITRE_MANQUANT);
      return;
    }

    setErreurTitre(null);
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
      <div className="flex flex-wrap items-center gap-3 px-4 pt-4 pb-2">
        <Button variant="ghost" size="icon" aria-label="Retour" onClick={handleCancel}>
          <ChevronLeft className="h-[18px] w-[18px]" />
        </Button>
        <h3 className="text-lg font-semibold text-text">
          {isEditing ? 'Modifier la tâche' : 'Nouvelle tâche'}
        </h3>

        <Button variant="primary" size="md" className="ml-auto" onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Spinner taille="bouton" className="mr-2" />
              Enregistrement...
            </>
          ) : (
            <>
              <Save className="h-[18px] w-[18px] mr-2" />
              Enregistrer
            </>
          )}
        </Button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Réservée aux échecs de sauvegarde : un titre manquant se dit sous
            son champ, pas dans un bandeau. */}
        {error && (
          <Alerte icone={<AlertCircle className="h-[18px] w-[18px]" />}>{error}</Alerte>
        )}

        <FormField
          label="Titre"
          htmlFor="taskform-titre"
          required
          error={erreurTitre ?? undefined}
        >
          <Input
            id="taskform-titre"
            type="text"
            required
            aria-required="true"
            error={Boolean(erreurTitre)}
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              // La demande tombe dès que le titre n'est plus vide : sinon le
              // champ garde sa bordure rouge, son `aria-invalid` et son
              // message pendant qu'on tape un titre valide sous les yeux.
              if (e.target.value.trim()) setErreurTitre(null);
            }}
            placeholder="Titre de la tâche"
          />
        </FormField>

        <FormField label="Description" htmlFor="taskform-description">
          <Textarea
            id="taskform-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description de la tâche"
            rows={4}
            className="resize-none"
          />
        </FormField>

        {/* Statut et Priorité restent côte à côte. */}
        <div className="grid grid-cols-2 gap-4">
          <FormField label="Statut" htmlFor="taskform-statut">
            <Select
              id="taskform-statut"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              options={OPTIONS_STATUT}
            />
          </FormField>

          <FormField label="Priorité" htmlFor="taskform-priorite">
            <Select
              id="taskform-priorite"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              options={OPTIONS_PRIORITE}
            />
          </FormField>
        </div>

        <FormField label="Date limite" htmlFor="taskform-date-limite">
          <Input
            id="taskform-date-limite"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </FormField>

        <FormField
          label="Tags"
          htmlFor="taskform-tags"
          description="Séparez les tags par des virgules"
        >
          <Input
            id="taskform-tags"
            type="text"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="design, urgent, client"
          />
        </FormField>

        {/* Project (optional, future feature) */}
        {/* <div>
          <label htmlFor="taskform-projet-lie" className="text-sm text-text-muted mb-2 block">Projet lié</label>
          <select id="taskform-projet-lie"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          >
            <option value="">Aucun</option>
          </select>
        </div> */}
      </div>
    </motion.div>
  );
}
