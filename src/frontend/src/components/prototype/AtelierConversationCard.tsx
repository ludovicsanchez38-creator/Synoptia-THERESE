import { useMemo, useState, type ReactNode } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Code2,
  ExternalLink,
  FileCode2,
  GitBranch,
  History,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Square,
  TestTube2,
  XCircle,
} from 'lucide-react';
import type { AgentTaskResponse, DiffResponse } from '../../services/api/agents';
import { CharacterPortrait } from './DecisionMissionPrototype';
import type {
  AtelierRunState,
  AtelierWorkspaceData,
} from './usePrototypeAtelierData';
import type { ReadResource } from './usePrototypeReadData';

export type AtelierTarget = string | 'new-mission' | 'current' | null;
export type AtelierReviewAction = 'approve' | 'reject' | 'rollback';

function StateShell({ children }: { children: ReactNode }) {
  return <div className="flex min-h-48 items-center justify-center px-5 py-8">{children}</div>;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date inconnue' : date.toLocaleString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: 'En attente', in_progress: 'En cours', review: 'À valider',
    done: 'Terminée sans changement', merged: 'Appliquée', rejected: 'Refusée',
    cancelled: 'Annulée', error: 'En erreur',
  };
  return labels[status] || status;
}

function statusClasses(status: string): string {
  if (status === 'review') return 'bg-[var(--color-warning-tint)] text-warning';
  if (status === 'merged' || status === 'done') return 'bg-[var(--color-success-tint)] text-success';
  if (status === 'in_progress' || status === 'pending') return 'bg-accent-tint text-accent';
  if (status === 'error' || status === 'rejected') return 'bg-[var(--color-error-tint)] text-error';
  return 'bg-surface-2 text-text-muted';
}

export function AtelierHistoryCard({
  resource,
  run,
  onRetry,
  onOpenTask,
  onNewMission,
  onOpenCurrent,
  onOpenClassic,
}: {
  resource: ReadResource<AtelierWorkspaceData>;
  run: AtelierRunState;
  onRetry: () => void;
  onOpenTask: (taskId: string) => void;
  onNewMission: () => void;
  onOpenCurrent: () => void;
  onOpenClassic: () => void;
}) {
  const tasks = resource.status === 'ready' ? resource.data.tasks.slice(0, 6) : [];
  const hasCurrentRun = run.status !== 'idle';

  return (
    <section aria-labelledby="atelier-history-title" className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]" data-testid="atelier-history-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <CharacterPortrait index={2} className="h-9 w-9 rounded-[9px] border border-text" />
          <div>
            <h2 id="atelier-history-title" className="text-sm font-semibold text-text">Atelier de code</h2>
            <p className="text-[11px] text-text-muted">{resource.status === 'ready' ? `${resource.data.total} mission${resource.data.total > 1 ? 's' : ''} enregistrée${resource.data.total > 1 ? 's' : ''}` : 'Lecture de l’historique local'}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={onNewMission} className="inline-flex items-center gap-1.5 rounded-[8px] bg-text px-2.5 py-1.5 text-[11px] font-semibold text-white"><Plus className="h-3.5 w-3.5" />Nouvelle mission</button>
          <button type="button" onClick={onOpenClassic} className="rounded-[8px] border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text">Atelier complet</button>
        </div>
      </div>

      {hasCurrentRun && (
        <button type="button" onClick={onOpenCurrent} className="flex w-full items-center gap-3 border-b border-[var(--k4)]/30 bg-[var(--k4bg)] px-4 py-3 text-left" data-testid="atelier-current-run">
          {run.status === 'running' ? <Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" /> : run.status === 'review' || run.status === 'done' ? <CheckCircle2 className="h-4 w-4 text-success" /> : <AlertCircle className="h-4 w-4 text-warning" />}
          <span className="min-w-0 flex-1"><strong className="block truncate text-xs text-text">{run.instruction || 'Mission Atelier'}</strong><span className="text-[11px] text-[var(--k4)]">{run.phase || statusLabel(run.status)}</span></span>
          <ChevronRight className="h-4 w-4 text-[var(--k4)]" />
        </button>
      )}

      {resource.status === 'loading' ? (
        <StateShell><div className="flex items-center gap-2 text-sm text-text-muted" role="status"><Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" />Je consulte les missions…</div></StateShell>
      ) : resource.status === 'error' ? (
        <StateShell><div className="max-w-sm text-center" data-testid="atelier-history-error"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">Atelier indisponible</p><p className="mt-1 text-xs leading-5 text-text-muted">{resource.error}</p><div className="mt-4 flex justify-center gap-2"><button type="button" onClick={onRetry} className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white"><RefreshCw className="h-3.5 w-3.5" />Réessayer</button><button type="button" onClick={onOpenClassic} className="rounded-[9px] border border-border px-3 py-2 text-xs font-semibold text-text">Ouvrir l’Atelier</button></div></div></StateShell>
      ) : tasks.length === 0 ? (
        <StateShell><div className="text-center" data-testid="atelier-history-empty"><Code2 className="mx-auto h-6 w-6 text-text-muted" /><p className="mt-2 text-sm font-semibold text-text">Aucune mission enregistrée</p><p className="mt-1 text-xs text-text-muted">Aucun fichier ne sera touché avant ta confirmation.</p><button type="button" onClick={onNewMission} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Préparer une mission</button></div></StateShell>
      ) : (
        <div className="divide-y divide-border">
          {tasks.map((task) => (
            <button key={task.id} type="button" onClick={() => onOpenTask(task.id)} className="flex w-full items-start gap-3 px-4 py-3.5 text-left hover:bg-surface-2">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[9px] bg-[var(--k4bg)] text-[var(--k4)]"><History className="h-4 w-4" /></span>
              <span className="min-w-0 flex-1"><strong className="block truncate text-sm text-text">{task.title}</strong><span className="mt-1 block text-[10px] text-text-muted">{formatDate(task.created_at)}{task.branch_name ? ` · ${task.branch_name}` : ''}</span></span>
              <span className={`rounded-full px-2 py-1 text-[9px] font-semibold ${statusClasses(task.status)}`}>{statusLabel(task.status)}</span>
              <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-text-muted" />
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function RepositoryPreflight({ workspace }: { workspace: AtelierWorkspaceData }) {
  const { status, config } = workspace;
  return (
    <section className="rounded-[13px] border border-border bg-surface p-4" data-testid="atelier-preflight">
      <div className="flex items-center gap-2 text-xs font-bold text-text"><ShieldCheck className="h-4 w-4 text-accent" />Périmètre réel de la mission</div>
      <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
        <div className="rounded-[9px] bg-surface-2 p-3"><dt className="text-[10px] uppercase tracking-wide text-text-muted">Dépôt autorisé</dt><dd className="mt-1 break-all font-semibold text-text">{status.repo_path || config.source_path || 'Non configuré'}</dd></div>
        <div className="rounded-[9px] bg-surface-2 p-3"><dt className="text-[10px] uppercase tracking-wide text-text-muted">État Git</dt><dd className="mt-1 font-semibold text-text">{status.current_branch || 'Branche inconnue'} · {status.working_tree_clean === true ? 'dépôt propre' : status.working_tree_clean === false ? 'changements non enregistrés' : 'état inconnu'}</dd></div>
        <div className="rounded-[9px] bg-surface-2 p-3"><dt className="text-[10px] uppercase tracking-wide text-text-muted">Katia</dt><dd className="mt-1 font-semibold text-text">{config.katia_model}</dd></div>
        <div className="rounded-[9px] bg-surface-2 p-3"><dt className="text-[10px] uppercase tracking-wide text-text-muted">Zézette</dt><dd className="mt-1 font-semibold text-text">{config.zezette_model}</dd></div>
      </dl>
    </section>
  );
}

function NewMissionForm({
  workspace,
  run,
  onStart,
}: {
  workspace: AtelierWorkspaceData;
  run: AtelierRunState;
  onStart: (instruction: string) => Promise<void>;
}) {
  const [instruction, setInstruction] = useState('');
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const blockers = useMemo(() => {
    const items: string[] = [];
    const status = workspace.status;
    if (!status.git_available) items.push('Git n’est pas disponible.');
    if (!status.repo_detected) items.push(status.repo_error || 'Le dépôt autorisé est introuvable.');
    if (status.current_branch && status.current_branch !== 'main') items.push(`La branche active est ${status.current_branch}, main est requise.`);
    if (status.working_tree_clean === false) items.push('Le dépôt contient des changements non enregistrés.');
    if (status.active_tasks > 0) items.push('Une autre mission est déjà en cours.');
    if (!status.katia_ready || !status.zezette_ready) items.push('La configuration de Katia ou Zézette est incomplète.');
    return items;
  }, [workspace]);

  function requestConfirmation() {
    if (instruction.trim().length < 15) {
      setError('Décris la mission en au moins 15 caractères.');
      return;
    }
    if (blockers.length > 0) {
      setError(blockers[0]);
      return;
    }
    setError(null);
    setConfirmationOpen(true);
  }

  return (
    <div className="space-y-4" data-testid="atelier-new-form">
      <RepositoryPreflight workspace={workspace} />
      <section className="rounded-[13px] border border-border bg-surface p-4">
        <label className="block text-xs font-semibold text-text">Mission à confier<textarea aria-label="Mission Atelier" value={instruction} onChange={(event) => setInstruction(event.target.value)} placeholder="Décris précisément le résultat attendu et ce qui ne doit pas changer…" className="mt-2 h-32 w-full resize-y rounded-[9px] border border-border p-3 text-sm font-normal leading-6 text-text outline-none focus:border-[var(--k4)]" /></label>
      </section>
      <section className="rounded-[13px] border border-accent-cyan/30 bg-accent-tint p-4 text-xs leading-5 text-accent">
        <strong>Ce qui sera autorisé après confirmation</strong>
        <ul className="mt-2 list-disc space-y-1 pl-4"><li>lire le dépôt et transmettre au modèle configuré les extraits utiles à la mission ;</li><li>écrire uniquement dans un worktree Git isolé sur une branche <code>agent/*</code> ;</li><li>lancer les commandes de test, lint et build autorisées, qui peuvent exécuter du code du dépôt ;</li><li>préparer un diff, sans l’appliquer à <code>main</code> avant une seconde confirmation.</li></ul>
        <p className="mt-2 font-semibold">Aucun email, devis, événement ou autre action métier externe n’est accessible depuis ce parcours.</p>
      </section>
      {blockers.length > 0 && <div className="rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning" role="alert"><strong>Mission bloquée pour protéger le dépôt.</strong><ul className="mt-1 list-disc pl-4">{blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul></div>}
      {error && <p className="text-xs font-semibold text-error" role="alert">{error}</p>}
      {confirmationOpen ? (
        <div className="rounded-[10px] border border-[var(--k4)]/30 bg-[var(--k4bg)] p-3" data-testid="atelier-confirmation">
          <div className="flex items-start gap-2 text-xs text-[var(--k4)]"><ShieldCheck className="h-4 w-4 shrink-0" /><div><strong>Confirmer l’exécution locale</strong><p className="mt-1">Katia cadrera la demande, puis Zézette pourra modifier le worktree et lancer les vérifications autorisées avec les modèles affichés ci-dessus.</p></div></div>
          <div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setConfirmationOpen(false)} className="rounded-[8px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Annuler</button><button type="button" disabled={run.status === 'running'} onClick={() => void onStart(instruction.trim())} className="inline-flex items-center gap-1.5 rounded-[8px] bg-[#047857] px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"><Play className="h-3.5 w-3.5 fill-current" />Confirmer et lancer</button></div>
        </div>
      ) : <div className="flex justify-end"><button type="button" onClick={requestConfirmation} disabled={blockers.length > 0} className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-45"><Code2 className="h-3.5 w-3.5" />Préparer la mission</button></div>}
    </div>
  );
}

function DiffViewer({ diff }: { diff: DiffResponse }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  return (
    <section className="rounded-[13px] border border-border bg-surface" data-testid="atelier-diff">
      <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3 text-xs"><strong className="text-text">Diff relu depuis {diff.branch_name}</strong><span className="text-success">+{diff.total_additions}</span><span className="text-error">-{diff.total_deletions}</span><span className="text-text-muted">{diff.files.length} fichier{diff.files.length > 1 ? 's' : ''}</span></div>
      <div className="divide-y divide-border">{diff.files.map((file) => <div key={file.file_path}><button type="button" onClick={() => setExpanded(expanded === file.file_path ? null : file.file_path)} className="flex w-full items-center gap-2 px-4 py-3 text-left text-xs hover:bg-surface-2">{expanded === file.file_path ? <ChevronDown className="h-3.5 w-3.5 text-text-muted" /> : <ChevronRight className="h-3.5 w-3.5 text-text-muted" />}<FileCode2 className="h-3.5 w-3.5 text-[var(--k4)]" /><span className="min-w-0 flex-1 truncate font-semibold text-text">{file.file_path}</span><span className="text-success">+{file.additions}</span><span className="text-error">-{file.deletions}</span></button>{expanded === file.file_path && file.diff_hunk && <pre className="max-h-80 overflow-auto bg-[#0A0F1E] p-4 text-[10px] leading-5 text-[#B6C7DA]">{file.diff_hunk}</pre>}</div>)}</div>
    </section>
  );
}

function ReviewControls({
  task,
  actionPending,
  onMutate,
}: {
  task: AgentTaskResponse;
  actionPending: AtelierReviewAction | null;
  onMutate: (taskId: string, action: AtelierReviewAction) => Promise<AgentTaskResponse | undefined>;
}) {
  const [confirmation, setConfirmation] = useState<AtelierReviewAction | null>(null);
  const canReview = task.status === 'review';
  const canRollback = task.status === 'merged';
  if (!canReview && !canRollback) return null;

  const label = confirmation === 'approve' ? 'appliquer ces changements sur main' : confirmation === 'reject' ? 'refuser et supprimer la branche Atelier' : 'annuler le merge par un nouveau commit Git';
  return (
    <section className="rounded-[13px] border border-border bg-surface p-4" data-testid="atelier-review-actions">
      {confirmation ? <div className="rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning"><strong>Confirmer : {label} ?</strong><p className="mt-1">L’action ne sera annoncée comme réussie qu’après relecture du statut backend.</p><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setConfirmation(null)} className="rounded-[8px] border border-border bg-surface px-3 py-2 font-semibold text-text">Retour</button><button type="button" disabled={actionPending !== null} onClick={() => { const action = confirmation; setConfirmation(null); void onMutate(task.id, action).catch(() => undefined); }} className="rounded-[8px] bg-text px-3 py-2 font-semibold text-white disabled:opacity-50">Confirmer l’action</button></div></div> : <div className="flex flex-wrap justify-end gap-2">{canReview && <><button type="button" onClick={() => setConfirmation('reject')} className="inline-flex items-center gap-1.5 rounded-[9px] border border-error bg-surface px-3 py-2 text-xs font-semibold text-error"><XCircle className="h-3.5 w-3.5" />Refuser</button><button type="button" onClick={() => setConfirmation('approve')} className="inline-flex items-center gap-1.5 rounded-[9px] bg-[#047857] px-3 py-2 text-xs font-semibold text-white"><CheckCircle2 className="h-3.5 w-3.5" />Appliquer sur main</button></>}{canRollback && <button type="button" onClick={() => setConfirmation('rollback')} className="inline-flex items-center gap-1.5 rounded-[9px] border border-[#B45309] bg-surface px-3 py-2 text-xs font-semibold text-warning"><RotateCcw className="h-3.5 w-3.5" />Annuler les changements</button>}</div>}
    </section>
  );
}

function TaskDetail({
  task,
  diffResource,
  actionPending,
  onMutate,
}: {
  task: AgentTaskResponse;
  diffResource: ReadResource<DiffResponse> | null;
  actionPending: AtelierReviewAction | null;
  onMutate: (taskId: string, action: AtelierReviewAction) => Promise<AgentTaskResponse | undefined>;
}) {
  return (
    <div className="space-y-4" data-testid="atelier-task-detail">
      <section className="rounded-[13px] border border-border bg-surface p-4"><div className="flex flex-wrap items-start justify-between gap-2"><div><span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted">Mission du {formatDate(task.created_at)}</span><h3 className="mt-2 text-base font-bold leading-6 text-text">{task.title}</h3></div><span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${statusClasses(task.status)}`}>{statusLabel(task.status)}</span></div>{task.description && <p className="mt-3 whitespace-pre-wrap border-t border-border pt-3 text-xs leading-5 text-text">{task.description}</p>}<div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-text-muted">{task.branch_name && <span className="flex items-center gap-1.5"><GitBranch className="h-3.5 w-3.5" />{task.branch_name}</span>}{task.base_branch && <span>Base : {task.base_branch}</span>}{task.commit_hash && <span>Commit : {task.commit_hash.slice(0, 12)}</span>}{task.agent_model && <span>Modèles : {task.agent_model}</span>}</div>{task.error && <div className="mt-3 rounded-[9px] bg-[var(--color-error-tint)] p-3 text-xs text-error">{task.error}</div>}</section>
      {task.plan && <section className="rounded-[13px] border border-border bg-surface p-4"><h4 className="text-xs font-bold text-text">Plan enregistré</h4><p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-text">{task.plan}</p></section>}
      {task.agent_outputs && Object.values(task.agent_outputs).some(Boolean) && <section className="grid gap-3 sm:grid-cols-2">{(['katia', 'zezette'] as const).map((agent) => task.agent_outputs?.[agent] ? <div key={agent} className="rounded-[12px] border border-border bg-surface p-3"><h4 className="text-xs font-bold capitalize text-text">{agent}</h4><p className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap text-[11px] leading-5 text-text">{task.agent_outputs[agent]}</p></div> : null)}</section>}
      {task.test_results && task.test_results.length > 0 && <section className="rounded-[13px] border border-border bg-surface p-4"><div className="flex items-center gap-2 text-xs font-bold text-text"><TestTube2 className="h-4 w-4 text-[var(--k4)]" />Vérifications enregistrées</div><div className="mt-3 space-y-2">{task.test_results.map((result, index) => <pre key={`${index}-${result.slice(0, 12)}`} className="max-h-52 overflow-auto whitespace-pre-wrap rounded-[9px] bg-[#0A0F1E] p-3 text-[10px] leading-5 text-[#B6C7DA]">{result}</pre>)}</div></section>}
      {task.explanation && <section className="rounded-[13px] border border-[var(--k4)]/30 bg-[var(--k4bg)] p-4"><h4 className="text-xs font-bold text-[var(--k4)]">Explication enregistrée</h4><p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-[var(--k4)]">{task.explanation}</p></section>}
      {task.diff_summary && <section className="rounded-[13px] border border-border bg-surface p-4"><h4 className="text-xs font-bold text-text">Résumé Git enregistré</h4><pre className="mt-2 whitespace-pre-wrap text-[11px] leading-5 text-text-muted">{task.diff_summary}</pre></section>}
      {diffResource?.status === 'loading' && <StateShell><div className="flex items-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Lecture du diff…</div></StateShell>}
      {diffResource?.status === 'error' && <div className="rounded-[10px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error" role="alert">{diffResource.error}</div>}
      {diffResource?.status === 'ready' && <DiffViewer diff={diffResource.data} />}
      <ReviewControls task={task} actionPending={actionPending} onMutate={onMutate} />
    </div>
  );
}

function AtelierRunView({
  run,
  taskResource,
  diffResource,
  actionPending,
  onCancel,
  onReset,
  onMutate,
}: {
  run: AtelierRunState;
  taskResource: ReadResource<AgentTaskResponse> | null;
  diffResource: ReadResource<DiffResponse> | null;
  actionPending: AtelierReviewAction | null;
  onCancel: () => Promise<void>;
  onReset: () => void;
  onMutate: (taskId: string, action: AtelierReviewAction) => Promise<AgentTaskResponse | undefined>;
}) {
  return (
    <div className="space-y-4" data-testid="atelier-run-view">
      <section className="rounded-[13px] border border-border bg-surface p-4"><span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted">Mission soumise</span><h3 className="mt-1 text-sm font-bold leading-6 text-text">{run.instruction}</h3>{run.taskId && <p className="mt-2 text-[10px] text-text-muted">Identifiant local : {run.taskId}</p>}</section>
      <div className="grid gap-3 sm:grid-cols-2">{(['katia', 'zezette'] as const).map((agentId, index) => { const agent = run.agents[agentId]; return <section key={agentId} className="rounded-[12px] border border-border bg-surface p-3"><div className="flex items-center gap-2.5"><CharacterPortrait index={index + 2} className="h-8 w-8 rounded-[8px] border border-text" /><div className="min-w-0 flex-1"><h4 className="text-xs font-bold text-text">{agentId === 'katia' ? 'Katia · cadrage' : 'Zézette · réalisation'}</h4><p className="text-[10px] text-text-muted">{agent.status === 'running' ? 'En cours' : agent.status === 'done' ? 'Terminé' : 'En attente'}</p></div>{agent.status === 'running' ? <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--k4)]" /> : agent.status === 'done' ? <CheckCircle2 className="h-3.5 w-3.5 text-success" /> : <span className="h-2 w-2 rounded-full bg-border" />}</div>{agent.content && <p className="mt-3 max-h-32 overflow-y-auto whitespace-pre-wrap text-[11px] leading-5 text-text">{agent.content}</p>}</section>; })}</div>
      {run.status === 'running' && <div className="rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3"><div className="flex items-center gap-2 text-xs font-semibold text-accent"><Loader2 className="h-4 w-4 animate-spin" />Phase réelle : {run.phase || 'démarrage'}</div></div>}
      {run.plan && <section className="rounded-[13px] border border-border bg-surface p-4"><h4 className="text-xs font-bold text-text">Plan transmis à Zézette</h4><p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-text">{run.plan}</p></section>}
      {run.events.length > 0 && <section className="rounded-[13px] border border-border bg-surface p-4"><h4 className="text-xs font-bold text-text">Journal de progression</h4><ol className="mt-2 space-y-2">{run.events.map((event) => <li key={event.id} className="flex gap-2 text-[11px] leading-5 text-text-muted"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#7C3AED]" /><span><strong className="text-text">{event.label}</strong>{event.content && event.type !== 'agent_done' ? <span className="block whitespace-pre-wrap">{event.content}</span> : null}</span></li>)}</ol></section>}
      <section className="rounded-[13px] border border-border bg-surface p-4"><div className="flex items-center gap-2 text-xs font-bold text-text"><TestTube2 className="h-4 w-4 text-[var(--k4)]" />Vérifications reçues</div>{run.tests.length > 0 ? <div className="mt-3 space-y-2">{run.tests.map((result, index) => <pre key={`${index}-${result.slice(0, 12)}`} className="max-h-52 overflow-auto whitespace-pre-wrap rounded-[9px] bg-[#0A0F1E] p-3 text-[10px] leading-5 text-[#B6C7DA]">{result}</pre>)}</div> : <p className="mt-2 text-xs text-text-muted">Aucun résultat de test ou de lint n’a été reçu. Aucun compteur de réussite n’est supposé.</p>}</section>
      {run.explanation && <section className="rounded-[13px] border border-[var(--k4)]/30 bg-[var(--k4bg)] p-4"><h4 className="text-xs font-bold text-[var(--k4)]">Explication de Katia</h4><p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-[var(--k4)]">{run.explanation}</p></section>}
      {(run.status === 'error' || run.status === 'persistence_error') && <div className="rounded-[10px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error" role="alert"><strong>Mission non validée.</strong><p className="mt-1">{run.error}</p></div>}
      {run.status === 'cancelled' && <div className="rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">Mission annulée. Le worktree temporaire est nettoyé par le backend.</div>}
      {taskResource?.status === 'ready' && (taskResource.data.status === 'review' || taskResource.data.status === 'merged') && <TaskDetail task={taskResource.data} diffResource={diffResource} actionPending={actionPending} onMutate={onMutate} />}
      {taskResource?.status === 'error' && <div className="rounded-[10px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error">{taskResource.error}</div>}
      <div className="flex justify-end">{run.status === 'running' ? <button type="button" onClick={() => void onCancel()} className="inline-flex items-center gap-1.5 rounded-[9px] border border-error bg-surface px-3 py-2 text-xs font-semibold text-error"><Square className="h-3.5 w-3.5 fill-current" />Annuler la mission</button> : <button type="button" onClick={onReset} className="rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Nouvelle mission</button>}</div>
    </div>
  );
}

export function AtelierWorkspaceCanvas({
  resource,
  taskResource,
  diffResource,
  run,
  target,
  actionPending,
  onRetry,
  onRetryTask,
  onStart,
  onCancel,
  onReset,
  onMutate,
  onOpenClassic,
}: {
  resource: ReadResource<AtelierWorkspaceData>;
  taskResource: ReadResource<AgentTaskResponse> | null;
  diffResource: ReadResource<DiffResponse> | null;
  run: AtelierRunState;
  target: AtelierTarget;
  actionPending: AtelierReviewAction | null;
  onRetry: () => void;
  onRetryTask: () => void;
  onStart: (instruction: string) => Promise<void>;
  onCancel: () => Promise<void>;
  onReset: () => void;
  onMutate: (taskId: string, action: AtelierReviewAction) => Promise<AgentTaskResponse | undefined>;
  onOpenClassic: () => void;
}) {
  const showRun = run.status !== 'idle' && (target === 'current' || target === 'new-mission');
  return (
    <div className="flex h-full flex-col"><div className="border-b border-border px-5 py-4 pr-16"><div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted"><Code2 className="h-3.5 w-3.5" />Atelier réel</div><h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">{target === 'new-mission' || target === 'current' ? 'Mission de changement' : 'Mission enregistrée'}</h2><p className="mt-1 text-sm text-text-muted">Cadrage, worktree isolé, progression réelle, diff Git et validation séparée.</p></div>
      <div className="min-h-0 flex-1 overflow-y-auto p-5">{resource.status === 'loading' ? <StateShell><div className="flex items-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Chargement de l’Atelier…</div></StateShell> : resource.status === 'error' ? <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{resource.error}</p><button type="button" onClick={onRetry} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell> : showRun ? <AtelierRunView run={run} taskResource={taskResource} diffResource={diffResource} actionPending={actionPending} onCancel={onCancel} onReset={onReset} onMutate={onMutate} /> : target === 'new-mission' || target === 'current' ? <NewMissionForm workspace={resource.data} run={run} onStart={onStart} /> : !taskResource || taskResource.status === 'loading' ? <StateShell><div className="flex items-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Chargement de la mission…</div></StateShell> : taskResource.status === 'error' ? <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{taskResource.error}</p><button type="button" onClick={onRetryTask} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell> : <TaskDetail task={taskResource.data} diffResource={diffResource} actionPending={actionPending} onMutate={onMutate} />}</div>
      <div className="border-t border-border bg-surface p-4"><button type="button" onClick={onOpenClassic} className="flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white"><ExternalLink className="h-4 w-4" />Ouvrir l’Atelier complet</button></div></div>
  );
}
