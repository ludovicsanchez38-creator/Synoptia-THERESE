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
import { useAbandonDeSaisie } from '../../hooks/useAbandonDeSaisie';
import { entreeValide } from '../../lib/entreeValide';

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

/** Marqueur de l'effet de chargement : le formulaire est en création. */
const NOUVELLE_TACHE = '(nouvelle tâche)';

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
  // B-974 : état de référence de la saisie ; null tant que la fiche à
  // modifier n'est pas chargée (la question reste alors posée).
  const [reference, setReference] = useState<string | null>(() =>
    currentTaskId ? null : JSON.stringify(['', '', 'todo', 'medium', '', '', '']),
  );
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
      setReference(JSON.stringify([
        task.title, task.description || '', task.status, task.priority,
        task.due_date ? task.due_date.split('T')[0] : '', task.project_id || '',
        task.tags ? task.tags.join(', ') : '',
      ]));
    } else if (!isEditing && tacheChargeeRef.current !== NOUVELLE_TACHE) {
      // B-989 : « Nouvelle tâche » pendant une modification gardait les champs
      // de la tâche ouverte, et l'enregistrement créait une copie. Le passage
      // à une création repart d'un formulaire vierge (la première ouverture
      // l'est déjà).
      const dejaOuvert = tacheChargeeRef.current !== null;
      tacheChargeeRef.current = NOUVELLE_TACHE;
      if (dejaOuvert) {
        setTitle(''); setDescription(''); setStatus('todo'); setPriority('medium');
        setDueDate(''); setProjectId(''); setTagsInput('');
        setReference(JSON.stringify(['', '', 'todo', 'medium', '', '', '']));
      }
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

    // B-998 : une tâche jamais chargée ne s'enregistre pas, ses valeurs par
    // défaut écraseraient la vraie tâche.
    if (isEditing && tacheChargeeRef.current !== currentTaskId) {
      setError('La tâche n’est pas encore chargée : réessaie dans un instant.');
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

      // B-998 : la modification suit l'identifiant ouvert, pas la présence de
      // la tâche dans `tasks` : un filtre la retirait de la liste et
      // l'enregistrement créait une copie.
      if (isEditing && currentTaskId) {
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

        const updated = await api.updateTask(currentTaskId, request);
        updateTaskInStore(currentTaskId, updated);
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

  // B-872 : plus de confirm() natif (D62/D106) ; la question se pose dans le
  // formulaire. B-973, B-974 : seulement si la saisie a changé, et Échap y
  // répond au lieu de fermer la vue (useAbandonDeSaisie).
  function abandonner() {
    clearDraft();
    setIsTaskFormOpen(false);
    setCurrentTask(null);
  }
  const modifie =
    reference === null ||
    JSON.stringify([title, description, status, priority, dueDate, projectId, tagsInput]) !== reference;
  const { abandonDemande, demanderAbandon: handleCancel, continuerSaisie, racineSaisie, questionRef } = useAbandonDeSaisie({ modifie, abandonner });

  return (
    <motion.div
      ref={racineSaisie}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="h-full flex flex-col"
      // B-1365 : Entrée dans un champ texte valide la tâche.
      onKeyDown={entreeValide(() => void handleSave(), saving)}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 px-4 pt-4 pb-2">
        <Button variant="ghost" size="icon" aria-label="Retour" onClick={handleCancel}>
          <ChevronLeft className="h-[18px] w-[18px]" />
        </Button>
        <h3 className="text-lg font-semibold text-text">
          {isEditing ? 'Modifier la tâche' : 'Nouvelle tâche'}
        </h3>
        {abandonDemande && (
          <div ref={questionRef} className="flex w-full flex-wrap items-center gap-2 rounded-sm border border-warning/40 bg-[var(--color-warning-tint)] px-3 py-2">
            <p role="alert" className="flex-1 text-sm font-semibold text-text">Abandonner les modifications ?</p>
            <Button variant="ghost" size="md" onClick={continuerSaisie}>Continuer la saisie</Button>
            <Button variant="danger" size="md" onClick={abandonner}>Abandonner</Button>
          </div>
        )}

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
          description="Sépare les étiquettes par des virgules"
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
