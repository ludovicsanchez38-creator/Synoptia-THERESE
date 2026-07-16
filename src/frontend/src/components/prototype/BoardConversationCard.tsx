import { useState, type ReactNode } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Gavel,
  Globe,
  History,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  ShieldCheck,
  Square,
  Users,
} from 'lucide-react';
import type {
  AdvisorInfo,
  AdvisorRole,
  BoardDecisionDetail,
  BoardMode,
  BoardRequest,
  BoardSynthesis,
} from '../../services/api/board';
import { CharacterPortrait } from './DecisionMissionPrototype';
import type { BoardRunState, BoardWorkspaceData, PrototypeAdvisorState } from './usePrototypeBoardData';
import type { ReadResource } from './usePrototypeReadData';
import { recordCloudConsent } from '../../lib/consent';

export type BoardTarget = string | 'new-board' | 'current' | null;

const advisorOrder: AdvisorRole[] = ['analyst', 'strategist', 'devil', 'pragmatic', 'visionary'];
const advisorPortraits: Record<AdvisorRole, number> = {
  analyst: 1, strategist: 2, devil: 3, pragmatic: 4, visionary: 5,
};

function StateShell({ children }: { children: ReactNode }) {
  return <div className="flex min-h-48 items-center justify-center px-5 py-8">{children}</div>;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date inconnue' : date.toLocaleString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function confidenceLabel(value: string): string {
  if (value === 'high') return 'Confiance élevée';
  if (value === 'medium') return 'Confiance moyenne';
  if (value === 'low') return 'Confiance faible';
  return value || 'Confiance inconnue';
}

export function BoardHistoryCard({
  resource,
  run,
  onRetry,
  onOpenDecision,
  onNewBoard,
  onOpenCurrent,
  onOpenClassic,
}: {
  resource: ReadResource<BoardWorkspaceData>;
  run: BoardRunState;
  onRetry: () => void;
  onOpenDecision: (decisionId: string) => void;
  onNewBoard: () => void;
  onOpenCurrent: () => void;
  onOpenClassic: () => void;
}) {
  const decisions = resource.status === 'ready' ? resource.data.decisions.slice(0, 5) : [];
  const hasCurrentRun = run.status !== 'idle';

  return (
    <section aria-labelledby="board-history-title" className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]" data-testid="board-history-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <CharacterPortrait index={1} className="h-9 w-9 rounded-[9px] border border-text" />
          <div>
            <h2 id="board-history-title" className="text-sm font-semibold text-text">Board de décision</h2>
            <p className="text-[11px] text-text-muted">{resource.status === 'ready' ? `${resource.data.decisions.length} décision${resource.data.decisions.length > 1 ? 's' : ''} enregistrée${resource.data.decisions.length > 1 ? 's' : ''}` : 'Lecture de l’historique local'}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={onNewBoard} className="inline-flex items-center gap-1.5 rounded-[8px] bg-text px-2.5 py-1.5 text-[11px] font-semibold text-white"><Plus className="h-3.5 w-3.5" />Nouvelle question</button>
          <button type="button" onClick={onOpenClassic} className="rounded-[8px] border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text">Board complet</button>
        </div>
      </div>

      {hasCurrentRun && (
        <button type="button" onClick={onOpenCurrent} className="flex w-full items-center gap-3 border-b border-[var(--k4)]/30 bg-[var(--k4bg)] px-4 py-3 text-left" data-testid="board-current-run">
          {run.status === 'running' ? <Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" /> : run.status === 'complete' ? <CheckCircle2 className="h-4 w-4 text-success" /> : <AlertCircle className="h-4 w-4 text-warning" />}
          <span className="min-w-0 flex-1"><strong className="block truncate text-xs text-text">{run.question}</strong><span className="text-[11px] text-[var(--k4)]">{run.phase || run.status}</span></span>
          <ChevronRight className="h-4 w-4 text-[var(--k4)]" />
        </button>
      )}

      {resource.status === 'loading' ? (
        <StateShell><div className="flex items-center gap-2 text-sm text-text-muted" role="status"><Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" />Je consulte les décisions…</div></StateShell>
      ) : resource.status === 'error' ? (
        <StateShell>
          <div className="max-w-sm text-center" data-testid="board-history-error"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">Historique indisponible</p><p className="mt-1 text-xs leading-5 text-text-muted">{resource.error}</p><div className="mt-4 flex justify-center gap-2"><button type="button" onClick={onRetry} className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white"><RefreshCw className="h-3.5 w-3.5" />Réessayer</button><button type="button" onClick={onOpenClassic} className="rounded-[9px] border border-border px-3 py-2 text-xs font-semibold text-text">Ouvrir le Board</button></div></div>
        </StateShell>
      ) : decisions.length === 0 ? (
        <StateShell><div className="text-center" data-testid="board-history-empty"><Gavel className="mx-auto h-6 w-6 text-text-muted" /><p className="mt-2 text-sm font-semibold text-text">Aucune décision enregistrée</p><p className="mt-1 text-xs text-text-muted">Une délibération ne démarrera qu’après ta confirmation.</p><button type="button" onClick={onNewBoard} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Convoquer le Board</button></div></StateShell>
      ) : (
        <div className="divide-y divide-border">
          {decisions.map((decision) => (
            <button key={decision.id} type="button" onClick={() => onOpenDecision(decision.id)} className="flex w-full items-start gap-3 px-4 py-3.5 text-left hover:bg-surface-2">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[9px] bg-[var(--k4bg)] text-[var(--k4)]"><History className="h-4 w-4" /></span>
              <span className="min-w-0 flex-1"><strong className="block truncate text-sm text-text">{decision.question}</strong><span className="mt-0.5 block truncate text-xs text-text-muted">{decision.recommendation}</span><span className="mt-1 block text-[10px] text-text-muted">{formatDate(decision.created_at)} · {decision.mode === 'sovereign' ? 'Souverain' : 'Cloud'} · {confidenceLabel(decision.confidence)}</span></span>
              <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-text-muted" />
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function SynthesisView({ synthesis }: { synthesis: BoardSynthesis }) {
  return (
    <div className="space-y-3" data-testid="board-synthesis">
      <section className="rounded-[13px] border border-success/40 bg-[var(--color-success-tint)] p-4"><div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-success">Recommandation</div><p className="mt-2 text-sm font-semibold leading-6 text-success">{synthesis.recommendation}</p><span className="mt-3 inline-block rounded-full bg-surface px-2.5 py-1 text-[10px] font-semibold text-success">{confidenceLabel(synthesis.confidence)}</span></section>
      <div className="grid gap-3 sm:grid-cols-2">
        <section className="rounded-[13px] border border-border bg-surface p-4"><h4 className="text-xs font-bold text-text">Consensus</h4><ul className="mt-2 space-y-2 text-xs leading-5 text-text">{synthesis.consensus_points.map((point) => <li key={point} className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />{point}</li>)}</ul></section>
        <section className="rounded-[13px] border border-warning/40 bg-[var(--color-warning-tint)] p-4"><h4 className="text-xs font-bold text-warning">Divergences</h4>{synthesis.divergence_points.length > 0 ? <ul className="mt-2 space-y-2 text-xs leading-5 text-warning">{synthesis.divergence_points.map((point) => <li key={point} className="flex gap-2"><AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{point}</li>)}</ul> : <p className="mt-2 text-xs text-warning">Aucune divergence enregistrée.</p>}</section>
      </div>
      <section className="rounded-[13px] border border-border bg-surface p-4"><h4 className="text-xs font-bold text-text">Prochaines étapes</h4><ol className="mt-2 space-y-2 text-xs leading-5 text-text">{synthesis.next_steps.map((step, index) => <li key={step} className="flex gap-2"><span className="font-bold text-[var(--k4)]">{index + 1}</span>{step}</li>)}</ol></section>
    </div>
  );
}

function AdvisorOpinionCard({ advisor, info }: { advisor?: PrototypeAdvisorState; info: AdvisorInfo }) {
  return (
    <section className="rounded-[12px] border border-border bg-surface p-3">
      <div className="flex items-center gap-2.5"><CharacterPortrait index={advisorPortraits[info.role]} className="h-8 w-8 rounded-[8px] border border-text" /><div className="min-w-0 flex-1"><h4 className="text-xs font-bold text-text">{info.name}</h4><p className="truncate text-[10px] text-text-muted">{advisor?.provider || info.personality}</p></div>{advisor?.isRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--k4)]" /> : advisor?.isComplete ? <CheckCircle2 className="h-3.5 w-3.5 text-success" /> : <span className="h-2 w-2 rounded-full bg-border" />}</div>
      {advisor?.content && <p className="mt-3 whitespace-pre-wrap text-xs leading-5 text-text">{advisor.content}</p>}
    </section>
  );
}

function BoardRunView({ run, advisors, onCancel, onReset }: { run: BoardRunState; advisors: AdvisorInfo[]; onCancel: () => void; onReset: () => void }) {
  const completed = Object.values(run.advisors).filter((advisor) => advisor.isComplete).length;
  const [cancelConfirmationOpen, setCancelConfirmationOpen] = useState(false);
  return (
    <div className="space-y-4" data-testid="board-run-view">
      <section className="rounded-[13px] border border-border bg-surface p-4"><div className="flex items-start justify-between gap-3"><div><span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted">Question soumise</span><h3 className="mt-1 text-sm font-bold leading-6 text-text">{run.question}</h3></div><span className="rounded-full bg-[var(--k4bg)] px-2.5 py-1 text-[10px] font-semibold text-[var(--k4)]">{run.mode === 'sovereign' ? 'Souverain' : 'Cloud'}</span></div>{run.context && <p className="mt-3 border-t border-border pt-3 text-xs leading-5 text-text-muted">{run.context}</p>}</section>

      {run.status === 'running' && <div className="rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3"><div className="flex items-center gap-2 text-xs font-semibold text-accent">{run.isSearchingWeb ? <Globe className="h-4 w-4 animate-pulse" /> : <Loader2 className="h-4 w-4 animate-spin" />}{run.phase}</div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface"><div className="h-full bg-[#7C3AED] transition-[width]" style={{ width: `${Math.max(4, completed / 5 * 100)}%` }} /></div><div className="mt-1 text-right text-[10px] text-text-muted">{completed}/5 conseillers terminés</div></div>}

      <div className="grid gap-3 xl:grid-cols-2">{advisorOrder.map((role) => {
        const info = advisors.find((advisor) => advisor.role === role) || { role, name: role, emoji: '', color: '', personality: '' };
        return <AdvisorOpinionCard key={role} advisor={run.advisors[role]} info={info} />;
      })}</div>

      {run.synthesis && <SynthesisView synthesis={run.synthesis} />}
      {(run.status === 'error' || run.status === 'persistence_error') && <div className="rounded-[10px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error" role="alert"><strong>{run.status === 'persistence_error' ? 'Sauvegarde non vérifiée.' : 'Délibération incomplète.'}</strong><p className="mt-1">{run.error}</p><p className="mt-1">Les avis partiels restent visibles mais aucune conclusion ne doit être considérée comme sauvegardée.</p></div>}
      {run.status === 'cancelled' && <div className="rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">Délibération annulée. Aucun résultat complet n’est présenté comme une décision.</div>}
      {run.status === 'complete' && <div className="flex items-start gap-2 rounded-[10px] border border-success/40 bg-[var(--color-success-tint)] p-3 text-xs text-success"><CheckCircle2 className="h-4 w-4 shrink-0" /><span><strong>Décision enregistrée.</strong>{run.decisionId ? ` Identifiant : ${run.decisionId}` : ''}</span></div>}

      {run.status === 'running' && cancelConfirmationOpen ? <div className="rounded-[10px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error" data-testid="board-cancel-confirmation"><strong>Annuler la délibération engagée ?</strong><p className="mt-1">Les appels en cours seront interrompus. Tu peux aussi masquer ce canevas et laisser le Board continuer en arrière-plan.</p><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setCancelConfirmationOpen(false)} className="rounded-[8px] border border-border bg-surface px-3 py-2 font-semibold text-text">Continuer en arrière-plan</button><button type="button" onClick={() => { setCancelConfirmationOpen(false); onCancel(); }} className="rounded-[8px] bg-error px-3 py-2 font-semibold text-white">Confirmer l’annulation</button></div></div> : <div className="flex justify-end gap-2">{run.status === 'running' ? <button type="button" onClick={() => setCancelConfirmationOpen(true)} className="inline-flex items-center gap-1.5 rounded-[9px] border border-error bg-surface px-3 py-2 text-xs font-semibold text-error"><Square className="h-3.5 w-3.5 fill-current" />Annuler la délibération</button> : <button type="button" onClick={onReset} className="rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Nouvelle question</button>}</div>}
    </div>
  );
}

function NewBoardForm({ advisors, run, onStart }: { advisors: AdvisorInfo[]; run: BoardRunState; onStart: (request: BoardRequest) => Promise<void> }) {
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [mode, setMode] = useState<BoardMode>('cloud');
  const [confirmationSnapshot, setConfirmationSnapshot] = useState<(BoardRequest & { advisorCount: number }) | null>(null);
  const [error, setError] = useState<string | null>(null);

  function validateSnapshot(snapshot: BoardRequest): string | null {
    if (snapshot.question.trim().length < 10) {
      return 'La question doit contenir au moins 10 caractères.';
    }
    if (snapshot.mode !== 'cloud' && snapshot.mode !== 'sovereign') {
      return 'Le mode de délibération figé est invalide.';
    }
    return null;
  }

  function requestConfirmation() {
    const snapshot = {
      question: question.trim(),
      context: context.trim() || undefined,
      mode,
      advisorCount: advisors.length || 5,
    };
    const validationError = validateSnapshot(snapshot);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setConfirmationSnapshot(snapshot);
  }

  function confirmStart() {
    if (!confirmationSnapshot) return;
    const validationError = validateSnapshot(confirmationSnapshot);
    if (validationError) {
      setError(validationError);
      setConfirmationSnapshot(null);
      return;
    }
    if (confirmationSnapshot.mode === 'cloud') {
      recordCloudConsent(undefined, {
        provider: 'Board cloud',
        dataCategories: ['question', 'contexte utile', 'profil local utile', 'résultats web'],
      });
    }
    void onStart({
      question: confirmationSnapshot.question,
      context: confirmationSnapshot.context,
      mode: confirmationSnapshot.mode,
    });
  }

  return (
    <div className="space-y-4" data-testid="board-new-form">
      <fieldset disabled={confirmationSnapshot !== null} onChangeCapture={() => setConfirmationSnapshot(null)} className="contents disabled:opacity-70" data-testid="board-form-fields">
      <section className="rounded-[13px] border border-border bg-surface p-4"><label className="block text-xs font-semibold text-text">Question stratégique<textarea aria-label="Question stratégique" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Quelle décision veux-tu éclairer ?" className="mt-2 h-28 w-full resize-y rounded-[9px] border border-border p-3 text-sm font-normal leading-6 text-text outline-none focus:border-[var(--k4)]" /></label><label className="mt-3 block text-xs font-semibold text-text">Contexte utile, facultatif<textarea aria-label="Contexte du Board" value={context} onChange={(event) => setContext(event.target.value)} placeholder="Contraintes, hypothèses, chiffres ou échéance…" className="mt-2 h-24 w-full resize-y rounded-[9px] border border-border p-3 text-xs font-normal leading-5 text-text outline-none focus:border-[var(--k4)]" /></label></section>
      <section className="rounded-[13px] border border-border bg-surface p-4"><h3 className="text-xs font-bold text-text">Mode de délibération</h3><div className="mt-3 grid grid-cols-2 gap-2"><button type="button" onClick={() => setMode('cloud')} className={`rounded-[10px] border p-3 text-left ${mode === 'cloud' ? 'border-[var(--k4)] bg-[var(--k4bg)]' : 'border-border'}`}><Globe className="h-4 w-4 text-[var(--k4)]" /><strong className="mt-2 block text-xs text-text">Cloud</strong><span className="mt-1 block text-[10px] leading-4 text-text-muted">Providers configurés et recherche web.</span></button><button type="button" onClick={() => setMode('sovereign')} className={`rounded-[10px] border p-3 text-left ${mode === 'sovereign' ? 'border-[var(--k4)] bg-[var(--k4bg)]' : 'border-border'}`}><ShieldCheck className="h-4 w-4 text-[var(--k4)]" /><strong className="mt-2 block text-xs text-text">Souverain</strong><span className="mt-1 block text-[10px] leading-4 text-text-muted">Ollama local, sans recherche web.</span></button></div></section>
      <section className="rounded-[13px] border border-border bg-surface p-4"><div className="flex items-center gap-2 text-xs font-bold text-text"><Users className="h-4 w-4 text-[var(--k4)]" />Conseillers réellement configurés</div><div className="mt-3 grid grid-cols-5 gap-2">{advisorOrder.map((role) => { const advisor = advisors.find((item) => item.role === role); return <div key={role} className="text-center"><CharacterPortrait index={advisorPortraits[role]} className="mx-auto h-9 w-9 rounded-[8px] border border-text" /><span className="mt-1 block truncate text-[9px] text-text-muted">{advisor?.name || role}</span></div>; })}</div></section>
      </fieldset>
      {error && <p className="text-xs font-semibold text-error" role="alert">{error}</p>}
      {confirmationSnapshot && (
        <div className="rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3" data-testid="board-confirmation"><div className="flex items-start gap-2 text-xs text-accent"><ShieldCheck className="h-4 w-4 shrink-0" /><div><strong>Confirmer le lancement du Board</strong><p className="mt-1 font-semibold">Question : {confirmationSnapshot.question}</p>{confirmationSnapshot.context && <p>Contexte : {confirmationSnapshot.context}</p>}<p>Mode : {confirmationSnapshot.mode === 'cloud' ? 'Cloud avec recherche web' : 'Souverain via Ollama local'}</p><p>Conseillers : {confirmationSnapshot.advisorCount}</p><p className="mt-1 font-semibold">Le mode cloud transmet la question, le contexte, le profil local utile et les résultats web aux fournisseurs configurés. Jusqu’à six appels LLM peuvent consommer des crédits API.</p>{confirmationSnapshot.mode === 'sovereign' && <p className="mt-1 font-semibold">Ollama doit être disponible. Aucun repli cloud ne sera effectué.</p>}</div></div><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setConfirmationSnapshot(null)} className="rounded-[8px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Annuler</button><button type="button" disabled={run.status === 'running'} onClick={confirmStart} className="inline-flex items-center gap-1.5 rounded-[8px] bg-[#047857] px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"><Play className="h-3.5 w-3.5 fill-current" />Confirmer et lancer</button></div></div>
      )}
      {!confirmationSnapshot && <div className="flex justify-end"><button type="button" onClick={requestConfirmation} className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white"><Gavel className="h-3.5 w-3.5" />Préparer la délibération</button></div>}
    </div>
  );
}

function DecisionDetail({ decision }: { decision: BoardDecisionDetail }) {
  return (
    <div className="space-y-4" data-testid="board-decision-detail">
      <section className="rounded-[13px] border border-border bg-surface p-4">
        <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted">Décision du {formatDate(decision.created_at)}</span>
        <h3 className="mt-2 text-base font-bold leading-6 text-text">{decision.question}</h3>
        {decision.context && <p className="mt-3 border-t border-border pt-3 text-xs leading-5 text-text-muted">{decision.context}</p>}
      </section>
      <div className="grid gap-3 xl:grid-cols-2">
        {decision.opinions.map((opinion) => (
          <section key={opinion.role} className="rounded-[12px] border border-border bg-surface p-3">
            <div className="flex items-center gap-2">
              <CharacterPortrait index={advisorPortraits[opinion.role]} className="h-8 w-8 rounded-[8px] border border-text" />
              <div className="min-w-0 flex-1"><strong className="block text-xs text-text">{opinion.name}</strong>{(opinion.provider || opinion.model) && <span className="block truncate text-[9px] text-text-muted">{opinion.provider || 'provider inconnu'} · {opinion.model || 'modèle non mesuré'}{typeof opinion.cost_eur === 'number' ? ` · ${opinion.cost_eur.toFixed(4)} €` : ''}</span>}</div>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-xs leading-5 text-text">{opinion.content}</p>
          </section>
        ))}
      </div>
      <SynthesisView synthesis={decision.synthesis} />
      {decision.web_sources && decision.web_sources.length > 0 && <section className="rounded-[12px] border border-border bg-surface p-4"><h4 className="text-xs font-bold text-text">Sources web consultées</h4><div className="mt-3 space-y-2">{decision.web_sources.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="flex items-start gap-2 rounded-[9px] bg-surface-2 p-3 text-xs text-text hover:text-[var(--k4)]"><ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" /><span><strong className="block">{source.title || source.url}</strong>{source.snippet && <span className="mt-1 block text-[10px] leading-4 text-text-muted">{source.snippet}</span>}</span></a>)}</div></section>}
      {decision.synthesis_usage && (decision.synthesis_usage.provider || decision.synthesis_usage.model) && <div className="rounded-[10px] border border-accent-cyan/30 bg-accent-tint px-3 py-2 text-[10px] text-accent">Synthèse : {decision.synthesis_usage.provider || 'provider inconnu'} · {decision.synthesis_usage.model || 'modèle non mesuré'}{typeof decision.synthesis_usage.cost_eur === 'number' ? ` · ${decision.synthesis_usage.cost_eur.toFixed(4)} €` : ''}</div>}
    </div>
  );
}

export function BoardWorkspaceCanvas({
  resource,
  decisionResource,
  run,
  target,
  onRetry,
  onRetryDecision,
  onStart,
  onCancel,
  onReset,
  onOpenClassic,
}: {
  resource: ReadResource<BoardWorkspaceData>;
  decisionResource: ReadResource<BoardDecisionDetail> | null;
  run: BoardRunState;
  target: BoardTarget;
  onRetry: () => void;
  onRetryDecision: () => void;
  onStart: (request: BoardRequest) => Promise<void>;
  onCancel: () => void;
  onReset: () => void;
  onOpenClassic: () => void;
}) {
  const advisors = resource.status === 'ready' ? resource.data.advisors : [];
  const showRun = run.status !== 'idle' && (target === 'current' || target === 'new-board');

  return (
    <div className="flex h-full flex-col"><div className="border-b border-border px-5 py-4 pr-16"><div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted"><Gavel className="h-3.5 w-3.5" />Board réel</div><h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">{target === 'new-board' || target === 'current' ? 'Délibération stratégique' : 'Décision enregistrée'}</h2><p className="mt-1 text-sm text-text-muted">Cinq regards, leurs divergences et une synthèse sauvegardée dans l’historique local.</p></div>
      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {resource.status === 'loading' ? <StateShell><div className="flex items-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Chargement du Board…</div></StateShell>
          : resource.status === 'error' ? <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{resource.error}</p><button type="button" onClick={onRetry} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell>
          : showRun ? <BoardRunView run={run} advisors={advisors} onCancel={onCancel} onReset={onReset} />
          : target === 'new-board' || target === 'current' ? <NewBoardForm advisors={advisors} run={run} onStart={onStart} />
          : !decisionResource || decisionResource.status === 'loading' ? <StateShell><div className="flex items-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Chargement de la décision…</div></StateShell>
          : decisionResource.status === 'error' ? <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{decisionResource.error}</p><button type="button" onClick={onRetryDecision} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell>
          : <DecisionDetail decision={decisionResource.data} />}
      </div><div className="border-t border-border bg-surface p-4"><button type="button" onClick={onOpenClassic} className="flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white"><ExternalLink className="h-4 w-4" />Ouvrir le Board complet</button></div></div>
  );
}
