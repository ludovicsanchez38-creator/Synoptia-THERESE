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
    <section aria-labelledby="board-history-title" className="overflow-hidden rounded-[16px] border border-[#DCE4F1] bg-white shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]" data-testid="board-history-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E7ECF4] px-4 py-3">
        <div className="flex items-center gap-2.5">
          <CharacterPortrait index={1} className="h-9 w-9 rounded-[9px] border border-[#101C36]" />
          <div>
            <h2 id="board-history-title" className="text-sm font-semibold text-[#101C36]">Board de décision</h2>
            <p className="text-[11px] text-[#7B8AA3]">{resource.status === 'ready' ? `${resource.data.decisions.length} décision${resource.data.decisions.length > 1 ? 's' : ''} enregistrée${resource.data.decisions.length > 1 ? 's' : ''}` : 'Lecture de l’historique local'}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={onNewBoard} className="inline-flex items-center gap-1.5 rounded-[8px] bg-[#101C36] px-2.5 py-1.5 text-[11px] font-semibold text-white"><Plus className="h-3.5 w-3.5" />Nouvelle question</button>
          <button type="button" onClick={onOpenClassic} className="rounded-[8px] border border-[#DCE4F1] px-2.5 py-1.5 text-[11px] font-semibold text-[#33415C]">Board complet</button>
        </div>
      </div>

      {hasCurrentRun && (
        <button type="button" onClick={onOpenCurrent} className="flex w-full items-center gap-3 border-b border-[#E1D9F5] bg-[#F7F3FE] px-4 py-3 text-left" data-testid="board-current-run">
          {run.status === 'running' ? <Loader2 className="h-4 w-4 animate-spin text-[#7C3AED]" /> : run.status === 'complete' ? <CheckCircle2 className="h-4 w-4 text-[#047857]" /> : <AlertCircle className="h-4 w-4 text-[#B45309]" />}
          <span className="min-w-0 flex-1"><strong className="block truncate text-xs text-[#101C36]">{run.question}</strong><span className="text-[11px] text-[#6D4CC3]">{run.phase || run.status}</span></span>
          <ChevronRight className="h-4 w-4 text-[#7C3AED]" />
        </button>
      )}

      {resource.status === 'loading' ? (
        <StateShell><div className="flex items-center gap-2 text-sm text-[#5B6A82]" role="status"><Loader2 className="h-4 w-4 animate-spin text-[#7C3AED]" />Je consulte les décisions…</div></StateShell>
      ) : resource.status === 'error' ? (
        <StateShell>
          <div className="max-w-sm text-center" data-testid="board-history-error"><AlertCircle className="mx-auto h-5 w-5 text-[#B45309]" /><p className="mt-2 text-sm font-semibold text-[#101C36]">Historique indisponible</p><p className="mt-1 text-xs leading-5 text-[#5B6A82]">{resource.error}</p><div className="mt-4 flex justify-center gap-2"><button type="button" onClick={onRetry} className="inline-flex items-center gap-1.5 rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white"><RefreshCw className="h-3.5 w-3.5" />Réessayer</button><button type="button" onClick={onOpenClassic} className="rounded-[9px] border border-[#DCE4F1] px-3 py-2 text-xs font-semibold text-[#33415C]">Ouvrir le Board</button></div></div>
        </StateShell>
      ) : decisions.length === 0 ? (
        <StateShell><div className="text-center" data-testid="board-history-empty"><Gavel className="mx-auto h-6 w-6 text-[#7B8AA3]" /><p className="mt-2 text-sm font-semibold text-[#101C36]">Aucune décision enregistrée</p><p className="mt-1 text-xs text-[#5B6A82]">Une délibération ne démarrera qu’après ta confirmation.</p><button type="button" onClick={onNewBoard} className="mt-4 rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white">Convoquer le Board</button></div></StateShell>
      ) : (
        <div className="divide-y divide-[#EDF1F7]">
          {decisions.map((decision) => (
            <button key={decision.id} type="button" onClick={() => onOpenDecision(decision.id)} className="flex w-full items-start gap-3 px-4 py-3.5 text-left hover:bg-[#F8FAFD]">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[9px] bg-[#F0E9FC] text-[#7C3AED]"><History className="h-4 w-4" /></span>
              <span className="min-w-0 flex-1"><strong className="block truncate text-sm text-[#101C36]">{decision.question}</strong><span className="mt-0.5 block truncate text-xs text-[#5B6A82]">{decision.recommendation}</span><span className="mt-1 block text-[10px] text-[#7B8AA3]">{formatDate(decision.created_at)} · {decision.mode === 'sovereign' ? 'Souverain' : 'Cloud'} · {confidenceLabel(decision.confidence)}</span></span>
              <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-[#9AA7BB]" />
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
      <section className="rounded-[13px] border border-[#BFE4D2] bg-[#EDF9F3] p-4"><div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#176345]">Recommandation</div><p className="mt-2 text-sm font-semibold leading-6 text-[#123D2C]">{synthesis.recommendation}</p><span className="mt-3 inline-block rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold text-[#176345]">{confidenceLabel(synthesis.confidence)}</span></section>
      <div className="grid gap-3 sm:grid-cols-2">
        <section className="rounded-[13px] border border-[#DCE4F1] bg-white p-4"><h4 className="text-xs font-bold text-[#101C36]">Consensus</h4><ul className="mt-2 space-y-2 text-xs leading-5 text-[#33415C]">{synthesis.consensus_points.map((point) => <li key={point} className="flex gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#047857]" />{point}</li>)}</ul></section>
        <section className="rounded-[13px] border border-[#F0D9A8] bg-[#FFF8E8] p-4"><h4 className="text-xs font-bold text-[#805D16]">Divergences</h4>{synthesis.divergence_points.length > 0 ? <ul className="mt-2 space-y-2 text-xs leading-5 text-[#5F4818]">{synthesis.divergence_points.map((point) => <li key={point} className="flex gap-2"><AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{point}</li>)}</ul> : <p className="mt-2 text-xs text-[#6F5A2B]">Aucune divergence enregistrée.</p>}</section>
      </div>
      <section className="rounded-[13px] border border-[#DCE4F1] bg-white p-4"><h4 className="text-xs font-bold text-[#101C36]">Prochaines étapes</h4><ol className="mt-2 space-y-2 text-xs leading-5 text-[#33415C]">{synthesis.next_steps.map((step, index) => <li key={step} className="flex gap-2"><span className="font-bold text-[#7C3AED]">{index + 1}</span>{step}</li>)}</ol></section>
    </div>
  );
}

function AdvisorOpinionCard({ advisor, info }: { advisor?: PrototypeAdvisorState; info: AdvisorInfo }) {
  return (
    <section className="rounded-[12px] border border-[#DCE4F1] bg-white p-3">
      <div className="flex items-center gap-2.5"><CharacterPortrait index={advisorPortraits[info.role]} className="h-8 w-8 rounded-[8px] border border-[#101C36]" /><div className="min-w-0 flex-1"><h4 className="text-xs font-bold text-[#101C36]">{info.name}</h4><p className="truncate text-[10px] text-[#7B8AA3]">{advisor?.provider || info.personality}</p></div>{advisor?.isRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin text-[#7C3AED]" /> : advisor?.isComplete ? <CheckCircle2 className="h-3.5 w-3.5 text-[#047857]" /> : <span className="h-2 w-2 rounded-full bg-[#DCE4F1]" />}</div>
      {advisor?.content && <p className="mt-3 whitespace-pre-wrap text-xs leading-5 text-[#33415C]">{advisor.content}</p>}
    </section>
  );
}

function BoardRunView({ run, advisors, onCancel, onReset }: { run: BoardRunState; advisors: AdvisorInfo[]; onCancel: () => void; onReset: () => void }) {
  const completed = Object.values(run.advisors).filter((advisor) => advisor.isComplete).length;
  return (
    <div className="space-y-4" data-testid="board-run-view">
      <section className="rounded-[13px] border border-[#DCE4F1] bg-white p-4"><div className="flex items-start justify-between gap-3"><div><span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#7B8AA3]">Question soumise</span><h3 className="mt-1 text-sm font-bold leading-6 text-[#101C36]">{run.question}</h3></div><span className="rounded-full bg-[#F0E9FC] px-2.5 py-1 text-[10px] font-semibold text-[#6D4CC3]">{run.mode === 'sovereign' ? 'Souverain' : 'Cloud'}</span></div>{run.context && <p className="mt-3 border-t border-[#EDF1F7] pt-3 text-xs leading-5 text-[#5B6A82]">{run.context}</p>}</section>

      {run.status === 'running' && <div className="rounded-[10px] border border-[#CFE9EE] bg-[#F1FBFC] p-3"><div className="flex items-center gap-2 text-xs font-semibold text-[#315D69]">{run.isSearchingWeb ? <Globe className="h-4 w-4 animate-pulse" /> : <Loader2 className="h-4 w-4 animate-spin" />}{run.phase}</div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white"><div className="h-full bg-[#7C3AED] transition-[width]" style={{ width: `${Math.max(4, completed / 5 * 100)}%` }} /></div><div className="mt-1 text-right text-[10px] text-[#5B6A82]">{completed}/5 conseillers terminés</div></div>}

      <div className="grid gap-3 xl:grid-cols-2">{advisorOrder.map((role) => {
        const info = advisors.find((advisor) => advisor.role === role) || { role, name: role, emoji: '', color: '', personality: '' };
        return <AdvisorOpinionCard key={role} advisor={run.advisors[role]} info={info} />;
      })}</div>

      {run.synthesis && <SynthesisView synthesis={run.synthesis} />}
      {(run.status === 'error' || run.status === 'persistence_error') && <div className="rounded-[10px] border border-[#F1C5C5] bg-[#FFF1F1] p-3 text-xs text-[#8A1C1C]" role="alert"><strong>{run.status === 'persistence_error' ? 'Sauvegarde non vérifiée.' : 'Délibération incomplète.'}</strong><p className="mt-1">{run.error}</p><p className="mt-1">Les avis partiels restent visibles mais aucune conclusion ne doit être considérée comme sauvegardée.</p></div>}
      {run.status === 'cancelled' && <div className="rounded-[10px] border border-[#F0D9A8] bg-[#FFF8E8] p-3 text-xs text-[#805D16]">Délibération annulée. Aucun résultat complet n’est présenté comme une décision.</div>}
      {run.status === 'complete' && <div className="flex items-start gap-2 rounded-[10px] border border-[#BFE4D2] bg-[#EDF9F3] p-3 text-xs text-[#176345]"><CheckCircle2 className="h-4 w-4 shrink-0" /><span><strong>Décision enregistrée.</strong>{run.decisionId ? ` Identifiant : ${run.decisionId}` : ''}</span></div>}

      <div className="flex justify-end gap-2">{run.status === 'running' ? <button type="button" onClick={onCancel} className="inline-flex items-center gap-1.5 rounded-[9px] border border-[#A61B1B] bg-white px-3 py-2 text-xs font-semibold text-[#A61B1B]"><Square className="h-3.5 w-3.5 fill-current" />Annuler la délibération</button> : <button type="button" onClick={onReset} className="rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white">Nouvelle question</button>}</div>
    </div>
  );
}

function NewBoardForm({ advisors, run, onStart }: { advisors: AdvisorInfo[]; run: BoardRunState; onStart: (request: BoardRequest) => Promise<void> }) {
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [mode, setMode] = useState<BoardMode>('cloud');
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function requestConfirmation() {
    if (question.trim().length < 10) {
      setError('La question doit contenir au moins 10 caractères.');
      return;
    }
    setError(null);
    setConfirmationOpen(true);
  }

  return (
    <div className="space-y-4" data-testid="board-new-form">
      <section className="rounded-[13px] border border-[#DCE4F1] bg-white p-4"><label className="block text-xs font-semibold text-[#33415C]">Question stratégique<textarea aria-label="Question stratégique" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Quelle décision veux-tu éclairer ?" className="mt-2 h-28 w-full resize-y rounded-[9px] border border-[#DCE4F1] p-3 text-sm font-normal leading-6 text-[#101C36] outline-none focus:border-[#7C3AED]" /></label><label className="mt-3 block text-xs font-semibold text-[#33415C]">Contexte utile, facultatif<textarea aria-label="Contexte du Board" value={context} onChange={(event) => setContext(event.target.value)} placeholder="Contraintes, hypothèses, chiffres ou échéance…" className="mt-2 h-24 w-full resize-y rounded-[9px] border border-[#DCE4F1] p-3 text-xs font-normal leading-5 text-[#101C36] outline-none focus:border-[#7C3AED]" /></label></section>
      <section className="rounded-[13px] border border-[#DCE4F1] bg-white p-4"><h3 className="text-xs font-bold text-[#101C36]">Mode de délibération</h3><div className="mt-3 grid grid-cols-2 gap-2"><button type="button" onClick={() => setMode('cloud')} className={`rounded-[10px] border p-3 text-left ${mode === 'cloud' ? 'border-[#7C3AED] bg-[#F7F3FE]' : 'border-[#DCE4F1]'}`}><Globe className="h-4 w-4 text-[#7C3AED]" /><strong className="mt-2 block text-xs text-[#101C36]">Cloud</strong><span className="mt-1 block text-[10px] leading-4 text-[#5B6A82]">Providers configurés et recherche web.</span></button><button type="button" onClick={() => setMode('sovereign')} className={`rounded-[10px] border p-3 text-left ${mode === 'sovereign' ? 'border-[#7C3AED] bg-[#F7F3FE]' : 'border-[#DCE4F1]'}`}><ShieldCheck className="h-4 w-4 text-[#7C3AED]" /><strong className="mt-2 block text-xs text-[#101C36]">Souverain</strong><span className="mt-1 block text-[10px] leading-4 text-[#5B6A82]">Ollama local, sans recherche web.</span></button></div></section>
      <section className="rounded-[13px] border border-[#DCE4F1] bg-white p-4"><div className="flex items-center gap-2 text-xs font-bold text-[#101C36]"><Users className="h-4 w-4 text-[#7C3AED]" />Conseillers réellement configurés</div><div className="mt-3 grid grid-cols-5 gap-2">{advisorOrder.map((role) => { const advisor = advisors.find((item) => item.role === role); return <div key={role} className="text-center"><CharacterPortrait index={advisorPortraits[role]} className="mx-auto h-9 w-9 rounded-[8px] border border-[#101C36]" /><span className="mt-1 block truncate text-[9px] text-[#5B6A82]">{advisor?.name || role}</span></div>; })}</div></section>
      {error && <p className="text-xs font-semibold text-[#A61B1B]" role="alert">{error}</p>}
      {confirmationOpen && (
        <div className="rounded-[10px] border border-[#CFE9EE] bg-[#F1FBFC] p-3" data-testid="board-confirmation"><div className="flex items-start gap-2 text-xs text-[#315D69]"><ShieldCheck className="h-4 w-4 shrink-0" /><div><strong>Confirmer le lancement du Board</strong><p className="mt-1">Mode : {mode === 'cloud' ? 'Cloud avec recherche web' : 'Souverain via Ollama local'}</p><p>Conseillers : {advisors.length || 5}</p><p className="mt-1 font-semibold">Le mode cloud transmet la question, le contexte, le profil local utile et les résultats web aux fournisseurs configurés. Jusqu’à six appels LLM peuvent consommer des crédits API.</p>{mode === 'sovereign' && <p className="mt-1 font-semibold">Ollama doit être disponible. Aucun repli cloud ne sera effectué.</p>}</div></div><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setConfirmationOpen(false)} className="rounded-[8px] border border-[#DCE4F1] bg-white px-3 py-2 text-xs font-semibold text-[#33415C]">Annuler</button><button type="button" disabled={run.status === 'running'} onClick={() => { if (mode === 'cloud') recordCloudConsent(); void onStart({ question: question.trim(), context: context.trim() || undefined, mode }); }} className="inline-flex items-center gap-1.5 rounded-[8px] bg-[#047857] px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"><Play className="h-3.5 w-3.5 fill-current" />Confirmer et lancer</button></div></div>
      )}
      {!confirmationOpen && <div className="flex justify-end"><button type="button" onClick={requestConfirmation} className="inline-flex items-center gap-1.5 rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white"><Gavel className="h-3.5 w-3.5" />Préparer la délibération</button></div>}
    </div>
  );
}

function DecisionDetail({ decision }: { decision: BoardDecisionDetail }) {
  return (
    <div className="space-y-4" data-testid="board-decision-detail"><section className="rounded-[13px] border border-[#DCE4F1] bg-white p-4"><span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#7B8AA3]">Décision du {formatDate(decision.created_at)}</span><h3 className="mt-2 text-base font-bold leading-6 text-[#101C36]">{decision.question}</h3>{decision.context && <p className="mt-3 border-t border-[#EDF1F7] pt-3 text-xs leading-5 text-[#5B6A82]">{decision.context}</p>}</section><div className="grid gap-3 xl:grid-cols-2">{decision.opinions.map((opinion) => <section key={opinion.role} className="rounded-[12px] border border-[#DCE4F1] bg-white p-3"><div className="flex items-center gap-2"><CharacterPortrait index={advisorPortraits[opinion.role]} className="h-8 w-8 rounded-[8px] border border-[#101C36]" /><strong className="text-xs text-[#101C36]">{opinion.name}</strong></div><p className="mt-3 whitespace-pre-wrap text-xs leading-5 text-[#33415C]">{opinion.content}</p></section>)}</div><SynthesisView synthesis={decision.synthesis} /></div>
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
    <div className="flex h-full flex-col"><div className="border-b border-[#E4EAF3] px-5 py-4 pr-16"><div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#7B8AA3]"><Gavel className="h-3.5 w-3.5" />Board réel</div><h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-[#101C36]">{target === 'new-board' || target === 'current' ? 'Délibération stratégique' : 'Décision enregistrée'}</h2><p className="mt-1 text-sm text-[#5B6A82]">Cinq regards, leurs divergences et une synthèse sauvegardée dans l’historique local.</p></div>
      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {resource.status === 'loading' ? <StateShell><div className="flex items-center gap-2 text-sm text-[#5B6A82]"><Loader2 className="h-4 w-4 animate-spin" />Chargement du Board…</div></StateShell>
          : resource.status === 'error' ? <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-[#B45309]" /><p className="mt-2 text-sm font-semibold text-[#101C36]">{resource.error}</p><button type="button" onClick={onRetry} className="mt-4 rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell>
          : showRun ? <BoardRunView run={run} advisors={advisors} onCancel={onCancel} onReset={onReset} />
          : target === 'new-board' || target === 'current' ? <NewBoardForm advisors={advisors} run={run} onStart={onStart} />
          : !decisionResource || decisionResource.status === 'loading' ? <StateShell><div className="flex items-center gap-2 text-sm text-[#5B6A82]"><Loader2 className="h-4 w-4 animate-spin" />Chargement de la décision…</div></StateShell>
          : decisionResource.status === 'error' ? <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-[#B45309]" /><p className="mt-2 text-sm font-semibold text-[#101C36]">{decisionResource.error}</p><button type="button" onClick={onRetryDecision} className="mt-4 rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell>
          : <DecisionDetail decision={decisionResource.data} />}
      </div><div className="border-t border-[#E4EAF3] bg-white p-4"><button type="button" onClick={onOpenClassic} className="flex w-full items-center justify-center gap-2 rounded-[10px] bg-[#101C36] px-4 py-3 text-sm font-semibold text-white"><ExternalLink className="h-4 w-4" />Ouvrir le Board complet</button></div></div>
  );
}
