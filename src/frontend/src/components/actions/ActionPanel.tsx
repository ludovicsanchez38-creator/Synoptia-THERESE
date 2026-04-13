/**
 * THERESE v2 - ActionPanel
 *
 * Panneau lateral pour lancer et suivre les agents actionnables.
 * Affiche la liste des agents, le formulaire de parametres,
 * la progression en temps reel et le resultat final.
 */

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Play, Square, ChevronRight, Loader2,
  FileBarChart, UserCheck, CalendarCheck, Wallet, Radar, Handshake,
  CheckCircle2, AlertCircle, Clock, Zap,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useActionsStore } from '../../stores/actionsStore';
import type { ActionAgent, TaskState, TaskStep } from '../../services/api/actions';

/** Mapping icone -> composant Lucide */
const ICON_MAP: Record<string, LucideIcon> = {
  FileBarChart, UserCheck, CalendarCheck, Wallet, Radar, Handshake,
  CheckCircle2, AlertCircle, Clock, Zap,
};

/** Couleurs par categorie */
const CATEGORY_COLORS: Record<string, string> = {
  organisation: 'text-cyan-400',
  commercial: 'text-blue-400',
  finance: 'text-emerald-400',
  strategie: 'text-violet-400',
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
  const colorClass = CATEGORY_COLORS[agent.category] || 'text-cyan-400';

  return (
    <motion.button
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onClick={() => onSelect(agent)}
      className={cn(
        'w-full text-left p-4 rounded-xl',
        'bg-[#131B35]/60 hover:bg-[#1A2340] border border-white/5 hover:border-white/10',
        'transition-colors duration-150',
        'group cursor-pointer',
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn('p-2 rounded-lg bg-white/5', colorClass)}>
          <IconComp size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-white/90 truncate">
              {agent.name}
            </h3>
            <ChevronRight
              size={16}
              className="text-white/20 group-hover:text-white/50 transition-colors flex-shrink-0"
            />
          </div>
          <p className="text-xs text-white/40 mt-1 line-clamp-2">
            {agent.description}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[10px] text-white/30 bg-white/5 px-2 py-0.5 rounded-full">
              {agent.steps_count} etapes
            </span>
            <span className={cn('text-[10px] px-2 py-0.5 rounded-full bg-white/5', colorClass)}>
              {CATEGORY_LABELS[agent.category] || agent.category}
            </span>
          </div>
        </div>
      </div>
    </motion.button>
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
}: {
  agent: ActionAgent;
  onSubmit: (params: Record<string, string>) => void;
  onBack: () => void;
  isLoading: boolean;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const IconComp = ICON_MAP[agent.icon] || Zap;
  const colorClass = CATEGORY_COLORS[agent.category] || 'text-cyan-400';

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
      <div className="flex items-center gap-3 p-4 border-b border-white/5">
        <button
          onClick={onBack}
          className="p-1 rounded hover:bg-white/5 text-white/40 hover:text-white/70"
        >
          <ChevronRight size={16} className="rotate-180" />
        </button>
        <div className={cn('p-2 rounded-lg bg-white/5', colorClass)}>
          <IconComp size={18} />
        </div>
        <div>
          <h3 className="text-sm font-medium text-white/90">{agent.name}</h3>
          <p className="text-xs text-white/40">{agent.steps_count} etapes</p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col p-4 gap-4">
        <p className="text-xs text-white/50">{agent.description}</p>

        {agent.params.map((param) => (
          <div key={param.id} className="space-y-1.5">
            <label className="text-xs font-medium text-white/60">
              {param.label}
              {param.required && <span className="text-red-400 ml-1">*</span>}
            </label>
            {param.type === 'select' ? (
              <select
                value={values[param.id] || ''}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, [param.id]: e.target.value }))
                }
                className={cn(
                  'w-full px-3 py-2 rounded-lg text-sm',
                  'bg-[#0B1226] border border-white/10 text-white/80',
                  'focus:border-[#2451FF] focus:outline-none',
                )}
              >
                <option value="">Choisir...</option>
                {param.options.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={values[param.id] || ''}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, [param.id]: e.target.value }))
                }
                placeholder={param.placeholder}
                className={cn(
                  'w-full px-3 py-2 rounded-lg text-sm',
                  'bg-[#0B1226] border border-white/10 text-white/80',
                  'placeholder:text-white/20',
                  'focus:border-[#2451FF] focus:outline-none',
                )}
              />
            )}
          </div>
        ))}

        <div className="flex-1" />

        <button
          type="submit"
          disabled={!isValid || isLoading}
          className={cn(
            'w-full py-2.5 rounded-lg text-sm font-medium',
            'bg-[#2451FF] text-white hover:bg-[#2451FF]/80',
            'disabled:opacity-40 disabled:cursor-not-allowed',
            'transition-colors duration-150',
            'flex items-center justify-center gap-2',
          )}
        >
          {isLoading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Play size={16} />
          )}
          Lancer
        </button>
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
  const isDone = task.status === 'completed';
  const isError = task.status === 'error';
  const isCancelled = task.status === 'cancelled';

  const statusLabel = {
    pending: 'En attente...',
    running: 'En cours...',
    completed: 'Termine',
    cancelled: 'Annule',
    error: 'Erreur',
  }[task.status];

  const statusColor = {
    pending: 'text-yellow-400',
    running: 'text-cyan-400',
    completed: 'text-emerald-400',
    cancelled: 'text-white/40',
    error: 'text-red-400',
  }[task.status];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <div>
          <h3 className="text-sm font-medium text-white/90">{task.agent_name}</h3>
          <span className={cn('text-xs', statusColor)}>{statusLabel}</span>
        </div>
        {isRunning ? (
          <button
            onClick={onCancel}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs',
              'bg-red-500/10 text-red-400 hover:bg-red-500/20',
              'transition-colors',
            )}
          >
            <Square size={12} />
            Annuler
          </button>
        ) : (
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-white/5 text-white/40"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Barre de progression */}
      <div className="px-4 py-3">
        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            className={cn(
              'h-full rounded-full',
              isDone ? 'bg-emerald-400' : isError ? 'bg-red-400' : 'bg-[#22D3EE]',
            )}
            initial={{ width: 0 }}
            animate={{ width: `${Math.round(task.progress * 100)}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
        <p className="text-[10px] text-white/30 mt-1 text-right">
          {Math.round(task.progress * 100)}%
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
        <div className="border-t border-white/5 p-4">
          <p className="text-xs text-white/50 mb-2">Resultat insere dans le chat.</p>
        </div>
      )}
    </div>
  );
}

function StepItem({ step, index }: { step: TaskStep; index: number }) {
  const [expanded, setExpanded] = useState(
    step.status === 'running' || step.status === 'completed',
  );

  const statusIcon = {
    pending: <Clock size={14} className="text-white/20" />,
    running: <Loader2 size={14} className="text-cyan-400 animate-spin" />,
    completed: <CheckCircle2 size={14} className="text-emerald-400" />,
    skipped: <Clock size={14} className="text-white/20" />,
    error: <AlertCircle size={14} className="text-red-400" />,
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
        'rounded-lg border transition-colors',
        step.status === 'running'
          ? 'border-cyan-400/20 bg-cyan-400/5'
          : step.status === 'completed'
          ? 'border-emerald-400/10 bg-emerald-400/5'
          : step.status === 'error'
          ? 'border-red-400/10 bg-red-400/5'
          : 'border-white/5 bg-transparent',
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 p-3 text-left"
      >
        {statusIcon}
        <span className="text-xs text-white/70 flex-1">{step.label}</span>
        <ChevronRight
          size={12}
          className={cn(
            'text-white/20 transition-transform',
            expanded && 'rotate-90',
          )}
        />
      </button>
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
              <div
                className={cn(
                  'text-xs text-white/50 whitespace-pre-wrap',
                  'max-h-40 overflow-y-auto',
                  'bg-[#0B1226]/50 rounded-lg p-2',
                )}
              >
                {step.content}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {step.error && (
        <div className="px-3 pb-3">
          <p className="text-xs text-red-400">{step.error}</p>
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

  const handleQuickLaunch = useCallback(
    async (agent: ActionAgent) => {
      if (agent.params.length > 0) {
        selectAgent(agent);
      } else {
        try {
          selectAgent(null);
          await launchAction(agent.id);
        } catch {
          // Erreur geree par le store
        }
      }
    },
    [selectAgent, launchAction],
  );

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
    if (activeTask && (activeTask.status === 'running' || activeTask.status === 'pending')) {
      return (
        <button
          onClick={() => openPanel()}
          className="fixed bottom-4 right-4 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-[#131B35] border border-cyan-400/30 text-sm text-cyan-400 shadow-lg shadow-cyan-400/10 hover:bg-[#1A2340] transition-colors animate-pulse"
        >
          <Loader2 size={14} className="animate-spin" />
          {activeTask.agent_name || 'Action'} en cours...
          <span
            role="button"
            tabIndex={0}
            onClick={(e) => {
              e.stopPropagation();
              cancelAction(activeTask.task_id);
            }}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.stopPropagation(); cancelAction(activeTask.task_id); } }}
            className="ml-1 p-1 rounded-full bg-red-500/20 text-red-400 hover:bg-red-500/30"
          >
            <Square size={10} />
          </span>
        </button>
      );
    }
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: '100%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: '100%', opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className={cn(
          'fixed right-0 top-0 bottom-0 z-50',
          'w-[380px] max-w-[90vw]',
          'bg-[#0B1226] border-l border-white/5',
          'flex flex-col shadow-2xl',
        )}
      >
        {/* Header global */}
        {showList && (
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-[#22D3EE]" />
              <h2 className="text-sm font-medium text-white/80">Actions</h2>
            </div>
            <button
              onClick={closePanel}
              className="p-1 rounded hover:bg-white/5 text-white/40 hover:text-white/70"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Contenu */}
        <div className="flex-1 overflow-hidden">
          {showList && (
            <div className="h-full overflow-y-auto p-4 space-y-6">
              {Object.entries(grouped).map(([category, catAgents]) => (
                <div key={category}>
                  <h3 className={cn('text-xs font-semibold uppercase tracking-wider mb-3', CATEGORY_COLORS[category] || 'text-white/40')}>
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

              {agents.length === 0 && !isLoading && (
                <p className="text-sm text-white/30 text-center py-8">
                  Aucune action disponible.
                </p>
              )}

              {isLoading && (
                <div className="flex justify-center py-8">
                  <Loader2 size={24} className="text-white/20 animate-spin" />
                </div>
              )}
            </div>
          )}

          {showForm && selectedAgent && (
            <ParamsForm
              agent={selectedAgent}
              onSubmit={handleLaunch}
              onBack={() => selectAgent(null)}
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
  );
}
