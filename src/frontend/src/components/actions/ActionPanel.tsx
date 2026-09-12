/**
 * THERESE v2 - ActionPanel
 *
 * Panneau lateral pour lancer et suivre les agents actionnables.
 * Affiche la liste des agents, le formulaire de parametres,
 * la progression en temps reel et le resultat final.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Play, Square, ChevronRight, FileBarChart, UserCheck, CalendarCheck, Wallet, Radar, Handshake,
  CheckCircle2, AlertCircle, Clock, Zap,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useActionsStore } from '../../stores/actionsStore';
import type { ActionAgent, TaskState, TaskStep } from '../../services/api/actions';
import { Spinner } from '../ui/Spinner';
import { usePanneauCouvrant } from '../../hooks/usePanneauCouvrant';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { VoilePanneau } from '../prototype/VoilePanneau';
import { CompactMarkdown } from '../ui/CompactMarkdown';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { FormField } from '../ui/FormField';
import { Alerte } from '../ui/Alerte';
import { EtatVide } from '../ui/EtatVide';
import { Etiquette } from '../ui/Etiquette';

/** Mapping icone -> composant Lucide */
const ICON_MAP: Record<string, LucideIcon> = {
  FileBarChart, UserCheck, CalendarCheck, Wallet, Radar, Handshake,
  CheckCircle2, AlertCircle, Clock, Zap,
};

/** Couleurs par categorie */
const CATEGORY_COLORS: Record<string, string> = {
  organisation: 'text-agent-cyan',
  commercial: 'text-agent-blue',
  finance: 'text-agent-green',
  strategie: 'text-agent-purple',
};

/** Labels des categories */
const CATEGORY_LABELS: Record<string, string> = {
  organisation: 'Organisation',
  commercial: 'Commercial',
  finance: 'Finance',
  strategie: 'Strategie',
};

// ---------------------------------------------------------------------------
// Sous-composant : carte d'un agent
// ---------------------------------------------------------------------------

function AgentCard({
  agent,
  onSelect,
}: {
  agent: ActionAgent;
  onSelect: (agent: ActionAgent) => void;
}) {
  const IconComp = ICON_MAP[agent.icon] || Zap;
  const colorClass = CATEGORY_COLORS[agent.category] || 'text-agent-cyan';

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full"
    >
      <Button
        type="button"
        variant="secondary"
        data-agent-id={agent.id}
        onClick={() => onSelect(agent)}
        className="group h-auto w-full items-stretch justify-start p-4 text-left"
      >
      <div className="flex w-full items-start gap-3">
        <div className={cn('p-2 rounded-md bg-surface-2', colorClass)}>
          <IconComp size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-text truncate">
              {agent.name}
            </h3>
            <ChevronRight
              size={16}
              className="text-text-muted group-hover:text-text transition-colors flex-shrink-0"
            />
          </div>
          <p className="text-sm font-normal text-text-muted mt-1 line-clamp-2">
            {agent.description}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <Etiquette ton="neutre">
              {agent.steps_count} étapes
            </Etiquette>
            <Etiquette ton="info" className={colorClass}>
              {CATEGORY_LABELS[agent.category] || agent.category}
            </Etiquette>
          </div>
        </div>
      </div>
      </Button>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Sous-composant : formulaire de parametres
// ---------------------------------------------------------------------------

function ParamsForm({
  agent,
  onSubmit,
  onBack,
  isLoading,
  error,
}: {
  agent: ActionAgent;
  onSubmit: (params: Record<string, string>) => void;
  onBack: () => void;
  isLoading: boolean;
  /** P-051 : une erreur de lancement se lit dans la fiche, pas seulement dans la liste. */
  error?: string | null;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const IconComp = ICON_MAP[agent.icon] || Zap;
  const colorClass = CATEGORY_COLORS[agent.category] || 'text-agent-cyan';
  // P-051 : la fiche remplace la carte qui avait le focus ; elle le reprend
  // sur son titre pour qu'un clavier ne retombe pas sur le corps du document.
  const titreRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => { titreRef.current?.focus(); }, [agent.id]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(values);
  };

  const isValid = agent.params
    .filter((p) => p.required)
    .every((p) => values[p.id]?.trim());

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 p-4 border-b border-border">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Retour au catalogue"
          onClick={onBack}
        >
          <ChevronRight size={16} className="rotate-180" />
        </Button>
        <div className={cn('p-2 rounded-md bg-surface-2', colorClass)}>
          <IconComp size={18} />
        </div>
        <div>
          <h3 ref={titreRef} tabIndex={-1} className="text-sm font-medium text-text outline-none">{agent.name}</h3>
          <p className="text-xs text-text-muted">{agent.steps_count} étapes</p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col p-4 gap-4">
        <p className="text-sm text-text-muted">{agent.description}</p>
        {error && (
          <Alerte titre="Lancement impossible">
            {error}
          </Alerte>
        )}

        {agent.params.map((param) => (
          <FormField key={param.id} label={param.label} htmlFor={`action-param-${param.id}`} required={param.required}>
            {param.type === 'select' ? (
              <Select aria-label={param.label}
                id={`action-param-${param.id}`}
                value={values[param.id] || ''}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, [param.id]: e.target.value }))
                }
                placeholder="Choisir..."
                options={param.options.map((opt) => ({ value: opt, label: opt }))}
              />
            ) : (
              <Input aria-label={param.label}
                id={`action-param-${param.id}`}
                type="text"
                value={values[param.id] || ''}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, [param.id]: e.target.value }))
                }
                placeholder={param.placeholder}
              />
            )}
          </FormField>
        ))}

        <div className="flex-1" />

        <Button
          type="submit"
          variant="primary"
          disabled={!isValid || isLoading}
          className="w-full"
        >
          {isLoading ? (
            <Spinner taille="bouton" />
          ) : (
            <Play size={16} />
          )}
          Lancer
        </Button>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sous-composant : progression d'une tache
// ---------------------------------------------------------------------------

function TaskProgress({
  task,
  onCancel,
  onClose,
}: {
  task: TaskState;
  onCancel: () => void;
  onClose: () => void;
}) {
  const isRunning = task.status === 'running' || task.status === 'pending';
  // 0.47 : l'arrêt est DEMANDÉ, pas obtenu - l'étape en cours va à son
  // terme. Le panneau le dit tel quel au lieu d'annoncer « Annulé ».
  const isStopping = task.status === 'cancel_requested';
  const isDone = task.status === 'completed';
  const isError = task.status === 'error';
  // B-643 (Nadia, c4) : une tâche annulée gardait la progression posée par
  // le moteur (100 %) à côté d'étapes restées en attente. Annulée, elle
  // affiche la part des étapes réellement terminées.
  const progression =
    task.status === 'cancelled'
      ? task.steps.length
        ? task.steps.filter((s) => s.status === 'completed').length / task.steps.length
        : 0
      : task.progress;

  const statusLabel = {
    pending: 'En attente...',
    running: 'En cours...',
    cancel_requested: 'Arrêt demandé...',
    completed: 'Terminé',
    cancelled: 'Annulé',
    error: 'Erreur',
  }[task.status];

  const statusColor = {
    pending: 'text-warning',
    running: 'text-accent',
    cancel_requested: 'text-warning',
    completed: 'text-success',
    cancelled: 'text-text-muted',
    error: 'text-error',
  }[task.status];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-4 border-b border-border">
        <div>
          <h3 className="text-sm font-medium text-text">{task.agent_name}</h3>
          <span className={cn('text-sm', statusColor)}>{statusLabel}</span>
        </div>
        {isRunning ? (
          <Button
            type="button"
            variant="danger"
            onClick={onCancel}
          >
            <Square size={14} className="mr-2" />
            Annuler
          </Button>
        ) : isStopping ? (
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs text-warning">
            <Spinner taille="ligne" />
            Arrêt en cours
          </span>
        ) : (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Fermer"
          >
            <X size={16} />
          </Button>
        )}
      </div>

      {/* Barre de progression */}
      <div className="px-4 py-3">
        <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
          <motion.div
            className={cn(
              'h-full rounded-full',
              isDone ? 'bg-success' : isError ? 'bg-error' : 'bg-accent-fill',
            )}
            initial={{ width: 0 }}
            animate={{ width: `${Math.round(progression * 100)}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
        <p className="text-xs text-text-muted mt-1 text-right">
          {Math.round(progression * 100)}%
        </p>
      </div>

      {/* Etapes */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
        {task.steps.map((step, idx) => (
          <StepItem key={step.step_id} step={step} index={idx} />
        ))}
      </div>

      {/* Resultat final */}
      {isDone && task.result && (
        <div className="border-t border-border p-4">
          <p className="text-xs text-text-muted mb-2">Résultat inséré dans le chat.</p>
        </div>
      )}
    </div>
  );
}

function StepItem({ step, index: _index }: { step: TaskStep; index: number }) {
  const [expanded, setExpanded] = useState(
    step.status === 'running' || step.status === 'completed',
  );

  const statusIcon = {
    pending: <Clock size={14} className="text-text-muted" />,
    running: <Spinner taille="ligne" className="text-accent" />,
    completed: <CheckCircle2 size={14} className="text-success" />,
    skipped: <Clock size={14} className="text-text-muted" />,
    error: <AlertCircle size={14} className="text-error" />,
  }[step.status];

  // Auto-expand quand ca devient running
  useEffect(() => {
    if (step.status === 'running') {
      setExpanded(true);
    }
  }, [step.status]);

  return (
    <div
      className={cn(
        'rounded-md border transition-colors',
        step.status === 'running'
          ? 'border-accent/30 bg-accent-tint'
          : step.status === 'completed'
          ? 'border-success/30 bg-[var(--color-success-tint)]'
          : step.status === 'error'
          ? 'border-error/30 bg-[var(--color-error-tint)]'
          : 'border-border bg-transparent',
      )}
    >
      <Button
        type="button"
        variant="ghost"
        onClick={() => setExpanded(!expanded)}
        className="h-auto w-full justify-start gap-2 p-3 text-left"
      >
        {statusIcon}
        <span className="text-sm font-normal text-text-muted flex-1">{step.label}</span>
        <ChevronRight
          size={12}
          className={cn(
            'text-text-muted transition-transform',
            expanded && 'rotate-90',
          )}
        />
      </Button>
      <AnimatePresence>
        {expanded && step.content && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 pt-0">
              <CompactMarkdown
                className={cn(
                  'text-sm leading-5 text-text-muted',
                  'max-h-40 overflow-y-auto',
                  'bg-bg/50 rounded-md p-2',
                )}
              >
                {step.content}
              </CompactMarkdown>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {step.error && (
        <div className="px-3 pb-3">
          <p className="text-sm text-error">{step.error}</p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Composant principal
// ---------------------------------------------------------------------------

export function ActionPanel() {
  const {
    agents,
    selectedAgent,
    activeTask,
    isLoading,
    isPanelOpen,
    error,
    loadAgents,
    selectAgent,
    launchAction,
    cancelTask: cancelAction,
    closePanel,
    openPanel,
    setActiveTask,
  } = useActionsStore();

  // Charger les agents au montage
  useEffect(() => {
    if (isPanelOpen && agents.length === 0) {
      loadAgents();
    }
  }, [isPanelOpen, agents.length, loadAgents]);

  // B-644 (Nadia, c4) : à 1024 px, le panneau recouvrait dix commandes qui
  // restaient focalisables, sans voile ni `inert`. Même règle que les six
  // panneaux de la coque (0.48.1) : sous le seuil côte à côte, un voile se
  // voit et le fond devient inerte ; le clavier reste à la page.
  const estCouvrant = usePanneauCouvrant();
  const panneauRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(panneauRef, {
    active: isPanelOpen,
    onEscape: closePanel,
    isolateBackground: estCouvrant,
    piegeClavier: false,
  });

  const handleLaunch = useCallback(
    async (params: Record<string, string>) => {
      if (!selectedAgent) return;
      try {
        await launchAction(selectedAgent.id, params);
      } catch {
        // Erreur geree par le store
      }
    },
    [selectedAgent, launchAction],
  );

  // P-051 (Nadia, c4) : plus de lancement direct depuis la carte ; la fiche
  // confirme, même sans paramètre.
  const ouvrirLaFicheAgent = useActionsStore((s) => s.ouvrirLaFicheAgent);
  const handleQuickLaunch = useCallback(
    (agent: ActionAgent) => { ouvrirLaFicheAgent(agent); },
    [ouvrirLaFicheAgent],
  );
  // Retour au catalogue : la carte quittée reprend le focus.
  const [retourVers, setRetourVers] = useState<string | null>(null);
  useEffect(() => {
    if (selectedAgent || !retourVers) return;
    document.querySelector<HTMLElement>(`[data-agent-id="${retourVers}"]`)?.focus();
    setRetourVers(null);
  }, [selectedAgent, retourVers]);

  // Grouper par categorie
  const grouped = agents.reduce<Record<string, ActionAgent[]>>((acc, agent) => {
    const cat = agent.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(agent);
    return acc;
  }, {});

  // Vue a afficher
  const showTask = activeTask && !selectedAgent;
  const showForm = selectedAgent && !showTask;
  const showList = !showTask && !showForm;

  if (!isPanelOpen) {
    if (
      activeTask &&
      (activeTask.status === 'running' ||
        activeTask.status === 'pending' ||
        activeTask.status === 'cancel_requested')
    ) {
      // B-362 : deux commandes, deux boutons frères ; un contrôle focalisable
      // imbriqué dans un bouton est invalide et double l'arrêt de tabulation.
      return (
        <div className="fixed bottom-4 right-4 z-50 flex items-center rounded-full border border-border bg-surface shadow-sm animate-pulse">
          <Button
            type="button"
            variant="ghost"
            onClick={() => openPanel()}
            className="rounded-full pl-4 pr-3"
          >
            <Spinner taille="ligne" />
            {activeTask.status === 'cancel_requested'
              ? `${activeTask.agent_name || 'Action'} - Arrêt en cours...`
              : `${activeTask.agent_name || 'Action'} en cours...`}
          </Button>
          {activeTask.status !== 'cancel_requested' && (
            <Button
              type="button"
              variant="danger"
              size="icon"
              aria-label="Annuler l'action"
              onClick={() => cancelAction(activeTask.task_id)}
              className="mr-2 h-8 w-8 rounded-full"
            >
              <Square size={14} />
            </Button>
          )}
        </div>
      );
    }
    return null;
  }

  return (
    <>
      {estCouvrant && <VoilePanneau fixe />}
    <AnimatePresence>
      <motion.div
        ref={panneauRef}
        initial={{ x: '100%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: '100%', opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className={cn(
          'fixed right-0 top-0 bottom-0 z-50',
          'w-[380px] max-w-[90vw]',
          'bg-bg border-l border-border',
          'flex flex-col shadow-sm',
        )}
      >
        {/* Header global */}
        {showList && (
          <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-accent-cyan-ink" />
              <h2 className="text-sm font-medium text-text">Actions</h2>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={closePanel}
              aria-label="Fermer les actions"
            >
              <X size={16} />
            </Button>
          </div>
        )}

        {/* Contenu */}
        <div className="flex-1 overflow-hidden">
          {showList && (
            <div className="h-full overflow-y-auto p-4 space-y-6">
              {Object.entries(grouped).map(([category, catAgents]) => (
                <div key={category}>
                  <h3 className={cn('text-xs font-semibold uppercase tracking-wider mb-3', CATEGORY_COLORS[category] || 'text-text-muted')}>
                    {CATEGORY_LABELS[category] || category}
                  </h3>
                  <div className="space-y-2">
                    {catAgents.map((agent) => (
                      <AgentCard
                        key={agent.id}
                        agent={agent}
                        onSelect={handleQuickLaunch}
                      />
                    ))}
                  </div>
                </div>
              ))}

              {error && !isLoading && (
                <Alerte
                  titre="Impossible de charger les actions"
                  action={<Button type="button" variant="secondary" size="sm" onClick={() => void loadAgents()}>Réessayer</Button>}
                >
                  {error}
                </Alerte>
              )}

              {/* B-374 : un échec de chargement n'est pas une liste vide. */}
              {agents.length === 0 && !isLoading && !error && (
                <EtatVide titre="Aucune action disponible" />
              )}

              {isLoading && (
                <div className="flex justify-center py-8">
                  <Spinner taille="zone" className="text-text-muted" annonce="Chargement des actions" />
                </div>
              )}
            </div>
          )}

          {showForm && selectedAgent && (
            <ParamsForm
              agent={selectedAgent}
              onSubmit={handleLaunch}
              error={error}
              onBack={() => { setRetourVers(selectedAgent.id); selectAgent(null); }}
              isLoading={isLoading}
            />
          )}

          {showTask && activeTask && (
            <TaskProgress
              task={activeTask}
              onCancel={() => cancelAction(activeTask.task_id)}
              onClose={() => {
                setActiveTask(null);
                closePanel();
              }}
            />
          )}
        </div>
      </motion.div>
    </AnimatePresence>
    </>
  );
}
