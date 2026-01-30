import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  X,
  Send,
  History,
  ChevronLeft,
  Loader2,
  Trash2,
  BarChart3,
  Target,
  Flame,
  Wrench,
  Rocket,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { DeliberationView } from './DeliberationView';
import { modalVariants, overlayVariants } from '../../lib/animations';
import { cn } from '../../lib/utils';
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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resetDeliberation = useCallback(() => {
    setIsSearchingWeb(false);
    setAdvisorStates(new Map());
    setSynthesis(null);
    setIsSynthesizing(false);
    setIsComplete(false);
    setViewingDecision(null);
  }, []);

  const handleCloseAndReset = useCallback(() => {
    resetDeliberation();
    setViewState('input');
    setQuestion('');
    setContext('');
    onClose();
  }, [resetDeliberation, onClose]);

  const handleStartDeliberation = useCallback(async () => {
    if (!question.trim()) return;

    resetDeliberation();
    setViewState('deliberating');

    try {
      const stream = streamDeliberation({
        question: question.trim(),
        context: context.trim() || undefined,
      });

      for await (const chunk of stream) {
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
            setIsComplete(true);
            break;

          case 'error':
            console.error('Deliberation error:', chunk.content);
            break;
        }
      }
    } catch (error) {
      console.error('Stream error:', error);
    }
  }, [question, context, resetDeliberation]);

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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={cn(
              'fixed inset-4 md:inset-8 lg:inset-12',
              'bg-surface rounded-2xl border border-border',
              'z-50 overflow-hidden flex flex-col',
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
                  <Users className="w-5 h-5 text-accent-cyan" />
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
                  <Button variant="primary" size="sm" onClick={handleNewDeliberation}>
                    + Nouvelle question
                  </Button>
                )}
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <AnimatePresence mode="wait">
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
                      <div className="relative w-20 h-20 mx-auto mb-4">
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-accent-cyan/40 to-accent-magenta/40 blur-xl animate-pulse" />
                        <div className="relative w-full h-full rounded-2xl bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 border-2 border-accent-cyan/30 flex items-center justify-center">
                          <Users className="w-10 h-10 text-accent-cyan" />
                        </div>
                      </div>
                      <h3 className="text-xl font-semibold text-text mb-2">
                        Convoque ton Board
                      </h3>
                      <p className="text-text-muted">
                        5 conseillers IA t'apporteront des perspectives différentes sur ta décision stratégique
                      </p>
                    </div>

                    {/* Conseillers preview */}
                    <div className="flex flex-wrap justify-center gap-3 mb-8">
                      {[
                        { icon: BarChart3, name: 'Analyste', color: '#22D3EE' },
                        { icon: Target, name: 'Stratège', color: '#A855F7' },
                        { icon: Flame, name: 'Avocat du Diable', color: '#EF4444' },
                        { icon: Wrench, name: 'Pragmatique', color: '#F59E0B' },
                        { icon: Rocket, name: 'Visionnaire', color: '#E11D8D' },
                      ].map((advisor) => {
                        const Icon = advisor.icon;
                        return (
                          <div
                            key={advisor.name}
                            className={cn(
                              'px-3 py-2 rounded-lg',
                              'bg-surface-elevated border border-border',
                              'flex items-center gap-2'
                            )}
                          >
                            <Icon className="w-4 h-4" style={{ color: advisor.color }} />
                            <span className="text-sm text-text-muted">{advisor.name}</span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Question input */}
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-text mb-2">
                          Ta question stratégique
                        </label>
                        <textarea
                          ref={textareaRef}
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
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
                          onChange={(e) => setContext(e.target.value)}
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

                      <Button
                        variant="primary"
                        className="w-full"
                        onClick={handleStartDeliberation}
                        disabled={!question.trim()}
                      >
                        <Send className="w-4 h-4 mr-2" />
                        Convoquer le Board
                      </Button>
                    </div>
                  </motion.div>
                )}

                {/* Deliberation View */}
                {viewState === 'deliberating' && (
                  <motion.div
                    key="deliberating"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <DeliberationView
                      question={question}
                      isSearchingWeb={isSearchingWeb}
                      advisorStates={advisorStates}
                      synthesis={synthesis}
                      isSynthesizing={isSynthesizing}
                      isComplete={isComplete}
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
                                decision.confidence === 'medium' && 'text-yellow-400',
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
