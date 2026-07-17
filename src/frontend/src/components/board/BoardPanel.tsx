import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Send,
  History,
  ChevronLeft,
  Loader2,
  Trash2,
  FileDown,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { DeliberationView } from './DeliberationView';
import { ModeSelector, type BoardMode } from './ModeSelector';
import { AdvisorArcLayout } from './AdvisorArcLayout';
import { modalVariants, overlayVariants } from '../../lib/animations';
import { cn } from '../../lib/utils';
import { Z_LAYER } from '../../styles/z-layers';
import { hasCloudConsent } from '../../lib/consent';
import {
  streamDeliberation,
  listBoardDecisions,
  getBoardDecision,
  deleteBoardDecision,
  type AdvisorRole,
  type BoardSynthesis,
  type BoardDecisionResponse,
} from '../../services/api';

interface BoardPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

type ViewState = 'input' | 'deliberating' | 'history' | 'viewing';

interface AdvisorState {
  role: AdvisorRole;
  content: string;
  provider?: string;
  isLoading: boolean;
  isComplete: boolean;
}

export function BoardPanel({ isOpen, onClose }: BoardPanelProps) {
  const [viewState, setViewState] = useState<ViewState>('input');
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [isSearchingWeb, setIsSearchingWeb] = useState(false);
  const [advisorStates, setAdvisorStates] = useState<Map<AdvisorRole, AdvisorState>>(new Map());
  const [synthesis, setSynthesis] = useState<BoardSynthesis | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [decisions, setDecisions] = useState<BoardDecisionResponse[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [viewingDecision, setViewingDecision] = useState<{
    question: string;
    opinions: Array<{ role: AdvisorRole; content: string }>;
    synthesis: BoardSynthesis;
  } | null>(null);
  const [mode, setMode] = useState<BoardMode>('cloud');
  const [ollamaModels, setOllamaModels] = useState<Array<{ name: string; size: number; paramSize?: string }>>([]);
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [ollamaAvailable, setOllamaAvailable] = useState(false);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Check Ollama availability
  const checkOllama = useCallback(() => {
    fetch('http://localhost:11434/api/tags')
      .then((res) => res.json())
      .then((data) => {
        if (data.models?.length > 0) {
          setOllamaAvailable(true);
          setOllamaModels(
            data.models
              .map((m: { name: string; size: number; details?: { parameter_size?: string } }) => ({
                name: m.name,
                size: m.size || 0,
                paramSize: m.details?.parameter_size,
              }))
              .sort((a: { size: number }, b: { size: number }) => a.size - b.size)
          );
        } else {
          setOllamaAvailable(false);
        }
      })
      .catch(() => setOllamaAvailable(false));
  }, []);

  useEffect(() => {
    checkOllama();
  }, [checkOllama]);

  const handleModelChange = useCallback((role: string, model: string) => {
    setSelectedModels((prev) => ({ ...prev, [role]: model }));
  }, []);

  const resetDeliberation = useCallback(() => {
    setIsSearchingWeb(false);
    setAdvisorStates(new Map());
    setSynthesis(null);
    setIsSynthesizing(false);
    setIsComplete(false);
    setViewingDecision(null);
    setConfirmationOpen(false);
    setRunError(null);
  }, []);

  useEffect(() => {
    if (!isOpen) abortRef.current?.abort();
    return () => abortRef.current?.abort();
  }, [isOpen]);

  const handleCloseAndReset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    resetDeliberation();
    setViewState('input');
    setQuestion('');
    setContext('');
    onClose();
  }, [resetDeliberation, onClose]);

  // Harmonisation 17/07 : Échap doit fermer le Board comme tout modal de
  // l'app (constaté en recette : le modal restait ouvert et bloquait la page).
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleCloseAndReset();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, handleCloseAndReset]);

  const handleCancelDeliberation = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    resetDeliberation();
    setViewState('input');
  }, [resetDeliberation]);

  const validateStart = useCallback((): string | null => {
    if (question.trim().length < 10) {
      return 'La question doit contenir au moins 10 caractères.';
    }
    if (mode === 'cloud') {
      // Revue 0.40.1 (F4) : le Board sollicite PLUSIEURS fournisseurs cloud -
      // un consentement LLM quelconque (ex. OpenAI seul) ne suffit pas.
      if (!hasCloudConsent('llm', 'board')) {
        return 'Le Board cloud interroge plusieurs fournisseurs IA. Autorise-le dans Paramètres > Confidentialité > Consentements cloud, ou lance-le depuis la nouvelle interface qui te demandera confirmation.';
      }
    }
    if (mode === 'sovereign' && !ollamaAvailable) {
      return 'Ollama local est indisponible. Le mode souverain ne basculera pas vers le cloud.';
    }
    return null;
  }, [mode, ollamaAvailable, question]);

  const handlePrepareDeliberation = useCallback(() => {
    const error = validateStart();
    setRunError(error);
    if (!error) setConfirmationOpen(true);
  }, [validateStart]);

  const handleStartDeliberation = useCallback(async () => {
    const validationError = validateStart();
    if (validationError) {
      setRunError(validationError);
      setConfirmationOpen(false);
      return;
    }

    // Annuler une éventuelle délibération précédente
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    resetDeliberation();
    setViewState('deliberating');
    let receivedDone = false;

    try {
      const stream = streamDeliberation({
        question: question.trim(),
        context: context.trim() || undefined,
        mode,
        ollama_models: mode === 'sovereign' ? selectedModels : undefined,
      }, controller.signal);

      for await (const chunk of stream) {
        if (controller.signal.aborted) break;

        switch (chunk.type) {
          case 'web_search_start':
            setIsSearchingWeb(true);
            break;

          case 'web_search_done':
            setIsSearchingWeb(false);
            break;

          case 'advisor_start':
            if (chunk.role) {
              setAdvisorStates((prev) => {
                const next = new Map(prev);
                next.set(chunk.role!, {
                  role: chunk.role!,
                  content: '',
                  provider: chunk.provider,
                  isLoading: true,
                  isComplete: false,
                });
                return next;
              });
            }
            break;

          case 'advisor_chunk':
            if (chunk.role) {
              setAdvisorStates((prev) => {
                const next = new Map(prev);
                const current = next.get(chunk.role!);
                if (current) {
                  next.set(chunk.role!, {
                    ...current,
                    content: current.content + chunk.content,
                  });
                }
                return next;
              });
            }
            break;

          case 'advisor_done':
            if (chunk.role) {
              setAdvisorStates((prev) => {
                const next = new Map(prev);
                const current = next.get(chunk.role!);
                if (current) {
                  next.set(chunk.role!, {
                    ...current,
                    isLoading: false,
                    isComplete: true,
                  });
                }
                return next;
              });
            }
            break;

          case 'synthesis_start':
            setIsSynthesizing(true);
            break;

          case 'synthesis_chunk':
            try {
              const synthesisData = JSON.parse(chunk.content) as BoardSynthesis;
              setSynthesis(synthesisData);
              setIsSynthesizing(false);
            } catch {
              console.error('Failed to parse synthesis');
            }
            break;

          case 'done':
            receivedDone = true;
            setIsComplete(true);
            abortRef.current = null;
            break;

          case 'error':
            setRunError(chunk.content || 'Le Board a rencontré une erreur.');
            abortRef.current = null;
            return;
        }
      }
      if (!controller.signal.aborted && !receivedDone) {
        setRunError('La délibération s’est interrompue avant sa sauvegarde.');
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        // Annulation volontaire - pas d'erreur
        return;
      }
      setRunError('Impossible de terminer la délibération.');
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
    }
  }, [question, context, mode, selectedModels, resetDeliberation, validateStart]);

  const handleShowHistory = useCallback(async () => {
    setLoadingHistory(true);
    setViewState('history');
    try {
      const list = await listBoardDecisions(20);
      setDecisions(list);
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const handleViewDecision = useCallback(async (id: string) => {
    try {
      const decision = await getBoardDecision(id);
      setViewingDecision({
        question: decision.question,
        opinions: decision.opinions,
        synthesis: decision.synthesis,
      });
      setViewState('viewing');
    } catch (error) {
      console.error('Failed to load decision:', error);
    }
  }, []);

  const handleDeleteDecision = useCallback(async (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Don't trigger view
    if (!confirm('Supprimer cette décision ?')) return;

    try {
      await deleteBoardDecision(id);
      setDecisions((prev) => prev.filter((d) => d.id !== id));
    } catch (error) {
      console.error('Failed to delete decision:', error);
    }
  }, []);

  const handleBack = useCallback(() => {
    if (viewState === 'viewing') {
      setViewState('history');
      setViewingDecision(null);
    } else if (viewState === 'history') {
      setViewState('input');
    } else if (viewState === 'deliberating' && isComplete) {
      resetDeliberation();
      setQuestion('');
      setContext('');
      setViewState('input');
    }
  }, [viewState, isComplete, resetDeliberation]);

  const handleNewDeliberation = useCallback(() => {
    resetDeliberation();
    setQuestion('');
    setContext('');
    setViewState('input');
  }, [resetDeliberation]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed inset-0 bg-black/60 backdrop-blur-sm ${Z_LAYER.MODAL}`}
            onClick={handleCloseAndReset}
          />

          {/* Panel */}
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="Board de décision"
            data-testid="board-panel"
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={cn(
              'fixed inset-4 md:inset-8 lg:inset-12',
              'bg-surface rounded-2xl border border-border',
              Z_LAYER.MODAL, 'overflow-hidden flex flex-col',
              'shadow-2xl'
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
              <div className="flex items-center gap-3">
                {(viewState === 'history' || viewState === 'viewing' || (viewState === 'deliberating' && isComplete)) && (
                  <Button variant="ghost" size="icon" onClick={handleBack}>
                    <ChevronLeft className="w-5 h-5" />
                  </Button>
                )}
                <div className="flex items-center gap-2">
                  <svg viewBox="0 0 40 40" className="w-5 h-5" fill="none">
                    <circle cx="20" cy="20" r="5.5" fill="#E6EDF7" />
                    <circle cx="20" cy="8" r="3" stroke="#22D3EE" strokeWidth="1.5" />
                    <circle cx="31.4" cy="16.3" r="3" stroke="#A855F7" strokeWidth="1.5" />
                    <circle cx="27.1" cy="29.7" r="3" stroke="#EF4444" strokeWidth="1.5" />
                    <circle cx="12.9" cy="29.7" r="3" stroke="#F59E0B" strokeWidth="1.5" />
                    <circle cx="8.6" cy="16.3" r="3" stroke="#E11D8D" strokeWidth="1.5" />
                  </svg>
                  <h2 className="text-lg font-semibold text-text">
                    Board de Décision Stratégique
                  </h2>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {viewState === 'input' && (
                  <Button variant="ghost" size="sm" onClick={handleShowHistory}>
                    <History className="w-4 h-4 mr-2" />
                    Historique
                  </Button>
                )}
                {(viewState === 'history' || viewState === 'viewing' || (viewState === 'deliberating' && isComplete)) && (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled
                      title="Export PDF disponible prochainement"
                      className="opacity-40 cursor-not-allowed"
                    >
                      <FileDown className="w-4 h-4 mr-1.5" />
                      PDF
                      <span className="ml-1 px-1.5 py-0.5 bg-amber-500/20 text-amber-400 text-[10px] rounded">Bientôt</span>
                    </Button>
                    <Button variant="primary" size="sm" onClick={handleNewDeliberation}>
                      + Nouvelle question
                    </Button>
                  </>
                )}
                <Button variant="ghost" size="icon" aria-label="Fermer le Board" onClick={handleCloseAndReset}>
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <AnimatePresence mode="wait" initial={false}>
                {/* Input View */}
                {viewState === 'input' && (
                  <motion.div
                    key="input"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="max-w-2xl mx-auto"
                  >
                    {/* Avatar et intro */}
                    <div className="text-center mb-8">
                      <div className="relative w-16 h-16 mx-auto mb-4">
                        <div className="absolute inset-0 rounded-2xl bg-accent-cyan/30 blur-xl animate-pulse" />
                        <div className="relative w-full h-full rounded-2xl bg-accent-cyan/20 border-2 border-accent-cyan/30 flex items-center justify-center">
                          <svg viewBox="0 0 40 40" className="w-9 h-9" fill="none">
                            <circle cx="20" cy="20" r="5.5" fill="#E6EDF7" />
                            <circle cx="20" cy="8" r="3" stroke="#22D3EE" strokeWidth="1.5" />
                            <circle cx="31.4" cy="16.3" r="3" stroke="#A855F7" strokeWidth="1.5" />
                            <circle cx="27.1" cy="29.7" r="3" stroke="#EF4444" strokeWidth="1.5" />
                            <circle cx="12.9" cy="29.7" r="3" stroke="#F59E0B" strokeWidth="1.5" />
                            <circle cx="8.6" cy="16.3" r="3" stroke="#E11D8D" strokeWidth="1.5" />
                          </svg>
                        </div>
                      </div>
                      <h3 className="text-xl font-semibold text-text mb-2">
                        Convoque ton Board
                      </h3>
                      <p className="text-text-muted">
                        5 conseillers IA t'apporteront des perspectives différentes sur ta décision stratégique
                      </p>
                    </div>

                    {/* Mode selector */}
                    <div className="flex justify-center mb-4">
                      <ModeSelector
                        mode={mode}
                        onChange={setMode}
                        ollamaAvailable={ollamaAvailable}
                        onRefreshOllama={checkOllama}
                      />
                    </div>

                    {/* Conseillers arc layout */}
                    <AdvisorArcLayout
                      mode={mode}
                      ollamaModels={ollamaModels}
                      selectedModels={selectedModels}
                      onModelChange={handleModelChange}
                    />

                    {/* Question input */}
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-text mb-2">
                          Ta question stratégique
                        </label>
                        <textarea
                          ref={textareaRef}
                          value={question}
                          onChange={(e) => { setQuestion(e.target.value); setConfirmationOpen(false); setRunError(null); }}
                          placeholder="Ex: Dois-je passer ma société en SASU ?"
                          rows={3}
                          className={cn(
                            'w-full p-4 rounded-xl',
                            'bg-surface-elevated border border-border',
                            'text-text placeholder:text-text-muted',
                            'focus:outline-none focus:ring-2 focus:ring-accent-cyan/50',
                            'resize-none'
                          )}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-text mb-2">
                          Contexte (optionnel)
                        </label>
                        <textarea
                          value={context}
                          onChange={(e) => { setContext(e.target.value); setConfirmationOpen(false); }}
                          placeholder="Informations supplémentaires sur ta situation..."
                          rows={2}
                          className={cn(
                            'w-full p-4 rounded-xl',
                            'bg-surface-elevated border border-border',
                            'text-text placeholder:text-text-muted',
                            'focus:outline-none focus:ring-2 focus:ring-accent-cyan/50',
                            'resize-none'
                          )}
                        />
                      </div>

                      {runError && <p className="text-sm text-red-400" role="alert">{runError}</p>}

                      {confirmationOpen && (
                        <div className="rounded-xl border border-accent-cyan/30 bg-accent-cyan/10 p-4 text-sm text-text-muted" data-testid="board-confirmation">
                          <p className="font-semibold text-text">Confirmer le lancement</p>
                          <p className="mt-1">Mode : {mode === 'cloud' ? 'cloud avec recherche web' : 'souverain via Ollama local'}.</p>
                          <p className="mt-1">Le mode cloud transmet la question, le contexte, le profil local utile et les résultats web aux fournisseurs configurés. Jusqu’à six appels LLM peuvent consommer des crédits API.</p>
                          <div className="mt-3 flex justify-end gap-2">
                            <Button variant="ghost" size="sm" onClick={() => setConfirmationOpen(false)}>Annuler</Button>
                            <Button variant="primary" size="sm" onClick={() => void handleStartDeliberation()}>Confirmer et lancer</Button>
                          </div>
                        </div>
                      )}

                      {!confirmationOpen && <button
                        onClick={handlePrepareDeliberation}
                        disabled={question.trim().length < 10}
                        data-testid="board-submit-btn"
                        className={cn(
                          'w-full py-3 px-6 rounded-xl font-semibold text-white',
                          'bg-accent-cyan hover:bg-accent-cyan/90',
                          'hover:scale-[1.02] active:scale-[0.98] transition-all duration-200',
                          'shadow-[0_4px_20px_rgba(34,211,238,0.3)]',
                          'hover:shadow-[0_6px_24px_rgba(34,211,238,0.35)]',
                          'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100',
                          'flex items-center justify-center gap-2',
                        )}
                      >
                        <Send className="w-4 h-4" />
                        {mode === 'sovereign' ? 'Préparer la délibération souveraine' : 'Préparer le Board'}
                      </button>}
                    </div>
                  </motion.div>
                )}

                {/* Deliberation View */}
                {viewState === 'deliberating' && (
                  <motion.div
                    key="deliberating"
                    data-testid="board-result"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    {runError && <div className="mb-4 rounded-xl border border-red-400/30 bg-red-400/10 p-3 text-sm text-red-300" role="alert">{runError}</div>}
                    <DeliberationView
                      question={question}
                      isSearchingWeb={isSearchingWeb}
                      isSovereign={mode === 'sovereign'}
                      advisorStates={advisorStates}
                      synthesis={synthesis}
                      isSynthesizing={isSynthesizing}
                      isComplete={isComplete}
                      onCancel={!isComplete ? handleCancelDeliberation : undefined}
                      onNewDeliberation={handleNewDeliberation}
                      onClose={handleCloseAndReset}
                    />
                  </motion.div>
                )}

                {/* History View */}
                {viewState === 'history' && (
                  <motion.div
                    key="history"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="max-w-2xl mx-auto"
                  >
                    <h3 className="text-lg font-semibold text-text mb-4">
                      Historique des décisions
                    </h3>

                    {loadingHistory ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-6 h-6 animate-spin text-text-muted" />
                      </div>
                    ) : decisions.length === 0 ? (
                      <p className="text-center text-text-muted py-12">
                        Aucune décision enregistrée
                      </p>
                    ) : (
                      <div className="space-y-3">
                        {decisions.map((decision) => (
                          <div
                            key={decision.id}
                            className={cn(
                              'relative p-4 rounded-xl',
                              'bg-surface-elevated border border-border',
                              'hover:border-accent-cyan/30 transition-colors',
                              'group cursor-pointer'
                            )}
                            onClick={() => handleViewDecision(decision.id)}
                          >
                            <p className="font-medium text-text mb-1 line-clamp-2 pr-8">
                              {decision.question}
                            </p>
                            <div className="flex items-center gap-3 text-sm text-text-muted">
                              <span>{new Date(decision.created_at).toLocaleDateString('fr-FR')}</span>
                              <span>•</span>
                              <span className={cn(
                                decision.confidence === 'high' && 'text-green-400',
                                decision.confidence === 'medium' && 'text-warning',
                                decision.confidence === 'low' && 'text-red-400'
                              )}>
                                Confiance {decision.confidence}
                              </span>
                            </div>
                            {/* Delete button */}
                            <button
                              onClick={(e) => handleDeleteDecision(decision.id, e)}
                              className={cn(
                                'absolute top-3 right-3 p-2 rounded-lg',
                                'text-text-muted hover:text-red-400',
                                'hover:bg-red-400/10 transition-colors',
                                'opacity-0 group-hover:opacity-100'
                              )}
                              title="Supprimer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}

                {/* Viewing Decision */}
                {viewState === 'viewing' && viewingDecision && (
                  <motion.div
                    key="viewing"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <DeliberationView
                      question={viewingDecision.question}
                      advisorStates={new Map(
                        viewingDecision.opinions.map((op) => [
                          op.role,
                          { role: op.role, content: op.content, isLoading: false, isComplete: true },
                        ])
                      )}
                      synthesis={viewingDecision.synthesis}
                      isSynthesizing={false}
                      isComplete={true}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
