import { useState, useCallback, useRef, useEffect } from 'react';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { motion, AnimatePresence, useIsPresent } from 'framer-motion';
import type { ReactNode } from 'react';
import {
  X,
  Send,
  History,
  ChevronLeft,
  Trash2,
  FileDown,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Alerte } from '../ui/Alerte';
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
  getOllamaStatus,
  type AdvisorRole,
  type BoardSynthesis,
  type BoardDecisionResponse,
} from '../../services/api';
import { annulerDeliberation, couperTransport } from './annulerDeliberation';
import { Spinner } from '../ui/Spinner';
import { estModeleOllamaCloud } from '../../lib/ollamaCloud';

// B-1176 : la confiance s'affiche en français, comme la carte de synthèse.
const LIBELLES_CONFIANCE: Record<string, string> = { high: 'élevée', medium: 'moyenne', low: 'faible' };

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

/**
 * Coquille animée du dialog Board : porte le focus trap via useIsPresent pour
 * que la protection (Échap, isolation) tienne PENDANT l'animation de sortie
 * d'AnimatePresence - un trap piloté par isOpen lâchait 150 ms trop tôt et un
 * second Échap fermait la vue située dessous (revue harmonisation F1).
 */
function BoardDialogShell({
  onEscape,
  children,
}: {
  onEscape: () => void;
  children: ReactNode;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const isPresent = useIsPresent();
  useDialogFocusTrap(dialogRef, {
    active: isPresent,
    onEscape,
    isolateBackground: true,
  });

  return (
    <motion.div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-label="Décision"
      data-testid="board-panel"
      variants={modalVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={cn(
        'fixed inset-4 md:inset-8 lg:inset-12',
        'bg-surface rounded-md border border-border',
        Z_LAYER.MODAL, 'overflow-hidden flex flex-col',
        'shadow-2xl'
      )}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </motion.div>
  );
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
  // B-873 : une panne de l'Historique n'est pas un carnet vide.
  const [historyError, setHistoryError] = useState<string | null>(null);
  // B-872 : plus de confirm() natif (D62/D106) ; la suppression se confirme en ligne.
  const [decisionASupprimer, setDecisionASupprimer] = useState<string | null>(null);
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
  // B-1215 : Ollama répond mais n'a que des modèles Ollama Cloud.
  const [seulementDesModelesCloud, setSeulementDesModelesCloud] = useState(false);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  // B-640 : une demande de fermeture pendant la délibération attend confirmation.
  const [fermetureDemandee, setFermetureDemandee] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  // 0.47 : identifiant du ProcessingTask (premier événement SSE) - cible
  // du chemin canonique d'annulation.
  const processingTaskIdRef = useRef<string | null>(null);

  // Sonde Ollama par le moteur (B-842). Un `fetch` direct vers
  // localhost:11434 ignorait l'adresse configurée dans Réglages : un Ollama
  // distant était déclaré absent et le mode souverain restait grisé.
  const checkOllama = useCallback(() => {
    getOllamaStatus()
      .then((statut) => {
        // B-1172 : un modèle Ollama Cloud part chez ollama.com ; le mode
        // souverain le refuse (B-1156), l'écran ne le propose donc pas.
        const modeles = (statut.models ?? [])
          .filter((m) => !estModeleOllamaCloud(m.name))
          .map((m) => ({ name: m.name, size: m.size ?? 0 }))
          .sort((a, b) => a.size - b.size);
        setOllamaAvailable(statut.available && modeles.length > 0);
        setSeulementDesModelesCloud(statut.available && modeles.length === 0 && (statut.models ?? []).length > 0);
        setOllamaModels(modeles);
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
    // Revue Grok 0.70.0 (P2) : une demande de fermeture ne survit pas à la délibération.
    setFermetureDemandee(false);
  }, []);

  useEffect(() => {
    if (!isOpen) abortRef.current?.abort();
    return () => abortRef.current?.abort();
  }, [isOpen]);

  const handleCloseAndReset = useCallback(() => {
    // Board classique : fermer = annuler - par le chemin canonique, le
    // backend arrête réellement les conseillers (un abort seul ne coupait
    // que le transport). couperTransport capture le controller MAINTENANT
    // (revue F8 : la ref est nettoyée avant le repli asynchrone).
    // B-652 (ronde B, D2) : l'identifiant du traitement n'était remis à null
    // qu'au démarrage suivant ; chaque fermeture rejouait une demande d'arrêt
    // (409) sur une délibération finie. Lu puis effacé, une seule fois.
    const traitementACloturer = processingTaskIdRef.current;
    processingTaskIdRef.current = null;
    void annulerDeliberation(traitementACloturer, couperTransport(abortRef));
    resetDeliberation();
    setFermetureDemandee(false);
    setViewState('input');
    setQuestion('');
    setContext('');
    onClose();
  }, [resetDeliberation, onClose]);

  // #110 : une délibération tombée en erreur n'est plus « en cours » ; elle
  // n'a plus rien à annuler ni à protéger d'une fermeture.
  const deliberationEnCours = viewState === 'deliberating' && !isComplete && !runError;

  // B-640 (Nadia, c4) : Échap, le fond ou « Fermer » pendant une délibération
  // en cours demandent confirmation ; partout ailleurs, fermeture immédiate.
  const demanderFermeture = useCallback(() => {
    if (deliberationEnCours) {
      setFermetureDemandee(true);
      return;
    }
    handleCloseAndReset();
  }, [deliberationEnCours, handleCloseAndReset]);

  const handleCancelDeliberation = useCallback(() => {
    const traitementACloturer = processingTaskIdRef.current;
    processingTaskIdRef.current = null;
    void annulerDeliberation(traitementACloturer, couperTransport(abortRef));
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

    // Annuler une éventuelle délibération précédente. Passe 2 de revue
    // (P2-10) : couper le transport TOUT DE SUITE - attendre le chemin
    // canonique laissait l'ancien flux muter les états du nouveau run.
    // Le canonique part en parallèle (idempotent côté backend, et la
    // déconnexion seule est déjà résolue proprement par le nettoyage
    // détaché du routeur).
    if (abortRef.current) {
      const ancienTraitement = processingTaskIdRef.current;
      couperTransport(abortRef)();
      void annulerDeliberation(ancienTraitement, () => {});
    }
    const controller = new AbortController();
    abortRef.current = controller;
    processingTaskIdRef.current = null;

    resetDeliberation();
    setViewState('deliberating');
    let receivedDone = false;
    let receivedCancelled = false;

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
          case 'task':
            processingTaskIdRef.current = chunk.content || null;
            break;

          case 'cancelled':
            // Le backend confirme l'arrêt : rien à sauver, retour au calme
            // (revue F11 : ne pas requalifier l'annulation en panne).
            receivedCancelled = true;
            break;

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
              // B-914 : l'indicateur tournait sans fin, seule trace en console.
              setIsSynthesizing(false);
              setRunError('La synthèse du Board est illisible : les avis ci-dessus restent consultables, relance la délibération pour obtenir une synthèse.');
            }
            break;

          case 'done':
            receivedDone = true;
            setIsComplete(true);
            if (abortRef.current === controller) abortRef.current = null;
            break;

          case 'error':
            setRunError(chunk.content || 'Le Board a rencontré une erreur.');
            setFermetureDemandee(false);
            if (abortRef.current === controller) abortRef.current = null;
            return;
        }
      }
      if (receivedCancelled) {
        // Annulé depuis le panneau Traitements : retour au calme, sans
        // faux message de panne.
        resetDeliberation();
        setViewState('input');
      } else if (!controller.signal.aborted && !receivedDone) {
        setRunError('La délibération s’est interrompue avant sa sauvegarde.');
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        // Annulation volontaire - pas d'erreur
        return;
      }
      setRunError('Impossible de terminer la délibération.');
      setFermetureDemandee(false);
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
    }
  }, [question, context, mode, selectedModels, resetDeliberation, validateStart]);

  const handleShowHistory = useCallback(async () => {
    setLoadingHistory(true);
    setHistoryError(null);
    setDecisionASupprimer(null);
    setViewState('history');
    try {
      const list = await listBoardDecisions(20);
      setDecisions(list);
    } catch (error) {
      console.error('Failed to load history:', error);
      setHistoryError('Impossible de charger l’historique des décisions.');
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const handleViewDecision = useCallback(async (id: string) => {
    setHistoryError(null);
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
      // B-900 : l'échec était muet ; la liste, elle, dit sa panne (B-873).
      setHistoryError('Impossible d’ouvrir cette décision. Réessaie dans un instant.');
      setViewState('history');
    }
  }, []);

  const handleDeleteDecision = useCallback(async (id: string) => {
    setHistoryError(null);
    try {
      await deleteBoardDecision(id);
      setDecisions((prev) => prev.filter((d) => d.id !== id));
      setDecisionASupprimer(null);
    } catch (error) {
      console.error('Failed to delete decision:', error);
      setHistoryError('Impossible de supprimer cette décision. Réessaie dans un instant.');
    }
  }, []);

  const handleBack = useCallback(() => {
    if (viewState === 'viewing') {
      setViewState('history');
      setViewingDecision(null);
    } else if (viewState === 'history') {
      setViewState('input');
    } else if (viewState === 'deliberating' && (isComplete || runError)) {
      resetDeliberation();
      setQuestion('');
      setContext('');
      setViewState('input');
    }
  }, [viewState, isComplete, runError, resetDeliberation]);

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
            onClick={demanderFermeture}
          />

          {/* Panel */}
          <BoardDialogShell onEscape={demanderFermeture}>
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
              <div className="flex items-center gap-3">
                {(viewState === 'history' || viewState === 'viewing' || (viewState === 'deliberating' && (isComplete || runError))) && (
                  <Button variant="ghost" size="icon" onClick={handleBack} aria-label="Retour">
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
                    Décision
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
                      <span className="ml-1 px-1.5 py-0.5 bg-agent-amber/20 text-agent-amber text-xs rounded-sm">Bientôt</span>
                    </Button>
                    <Button variant="primary" size="sm" onClick={handleNewDeliberation}>
                      + Nouvelle question
                    </Button>
                  </>
                )}
                <Button variant="ghost" size="icon" aria-label="Fermer le Board" onClick={demanderFermeture}>
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* B-639 (Nadia, c4) : avec mode="wait" et des sorties animées, la vue
                  suivante ne montait qu'après la fin de sortie de la précédente. Or
                  après une bascule Cloud → Souverain, l'indicateur partagé du
                  sélecteur de mode (`layoutId`, retiré depuis dans ModeSelector)
                  empêchait toute sortie de se terminer : le formulaire restait
                  monté à opacité 0, toujours cliquable, et « Confirmer et lancer »
                  invisible lançait une seconde délibération. Chaque composant
                  motion de la vue sortante s'enregistre auprès de la présence et
                  peut retarder son démontage : les vues changent donc hors de tout
                  AnimatePresence (React démonte, rien ne reste coincé), l'animation
                  d'entrée est conservée. */}
              <>
                {/* Input View */}
                {viewState === 'input' && (
                  <motion.div
                    key="input"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="max-w-2xl mx-auto"
                  >
                    {/* Avatar et intro */}
                    <div className="text-center mb-8">
                      <div className="relative w-16 h-16 mx-auto mb-4">
                        <div className="absolute inset-0 rounded-md bg-accent-cyan/30 blur-xl animate-pulse" />
                        <div className="relative w-full h-full rounded-md bg-accent-cyan/20 border-2 border-accent-cyan/30 flex items-center justify-center">
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
                        raisonIndisponible={
                          seulementDesModelesCloud
                            ? 'Aucun modèle local installé : les modèles Ollama Cloud partent en ligne'
                            : undefined
                        }
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
                        <textarea aria-label="Question soumise au Board"
                          ref={textareaRef}
                          value={question}
                          onChange={(e) => { setQuestion(e.target.value); setConfirmationOpen(false); setRunError(null); }}
                          placeholder="Ex: Dois-je passer ma société en SASU ?"
                          rows={3}
                          className={cn(
                            'w-full p-4 rounded-md',
                            'bg-surface-elevated border border-border',
                            'text-text placeholder:text-text-muted',
                            'focus:outline-none focus:ring-2 focus:ring-ring/50',
                            'resize-none'
                          )}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-text mb-2">
                          Contexte (optionnel)
                        </label>
                        <textarea aria-label="Contexte de la décision"
                          value={context}
                          onChange={(e) => { setContext(e.target.value); setConfirmationOpen(false); }}
                          placeholder="Informations supplémentaires sur ta situation..."
                          rows={2}
                          className={cn(
                            'w-full p-4 rounded-md',
                            'bg-surface-elevated border border-border',
                            'text-text placeholder:text-text-muted',
                            'focus:outline-none focus:ring-2 focus:ring-ring/50',
                            'resize-none'
                          )}
                        />
                      </div>

                      {runError && <p className="text-sm text-error" role="alert">{runError}</p>}

                      {confirmationOpen && (
                        <div className="rounded-md border border-accent-cyan/30 bg-accent-cyan/10 p-4 text-sm text-text-muted" data-testid="board-confirmation">
                          <p className="font-semibold text-text">Confirmer le lancement</p>
                          <p className="mt-1">Mode : {mode === 'cloud' ? 'cloud avec recherche web' : 'souverain via Ollama local'}.</p>
                          {/* B-642 (Nadia, c4) : sous un lancement local, le paragraphe sur les crédits cloud faisait douter de ce qui allait partir. */}
                          {mode === 'cloud' ? (
                            <p className="mt-1">Le mode cloud transmet la question, le contexte, le profil local utile et les résultats web aux fournisseurs configurés. Jusqu’à six appels LLM peuvent consommer des crédits API.</p>
                          ) : (
                            <p className="mt-1">Tout reste sur cette machine : la question, le contexte et les avis passent par Ollama en local, un conseiller après l’autre. Aucun crédit n’est consommé et aucun repli vers le cloud n’aura lieu.</p>
                          )}
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
                          'w-full py-3 px-6 rounded-md font-semibold text-accent-ink',
                          'bg-accent-fill hover:opacity-90',
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
                  >
                    {runError && <div className="mb-4 rounded-md border border-error/30 bg-error/10 p-3 text-sm text-error" role="alert">{runError}</div>}
                    {/* B-640 (Nadia, c4) : fermer pendant la délibération jetait tout
                        sans un mot. La fermeture se confirme tant qu'elle tourne. */}
                    {fermetureDemandee && deliberationEnCours && (
                      <div
                        role="alertdialog"
                        aria-label="Délibération en cours"
                        className="mb-4 rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-sm text-text"
                      >
                        <p className="font-semibold">Une délibération est en cours.</p>
                        <p className="mt-1 text-text-muted">
                          Fermer maintenant l’annule : les avis déjà obtenus ne seront pas enregistrés dans l’Historique.
                        </p>
                        <div className="mt-3 flex justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={() => setFermetureDemandee(false)}>Continuer la délibération</Button>
                          <Button variant="primary" size="sm" onClick={handleCloseAndReset}>Annuler et fermer</Button>
                        </div>
                      </div>
                    )}
                    <DeliberationView
                      question={question}
                      isSearchingWeb={isSearchingWeb}
                      isSovereign={mode === 'sovereign'}
                      advisorStates={advisorStates}
                      synthesis={synthesis}
                      isSynthesizing={isSynthesizing}
                      isComplete={isComplete}
                      onCancel={deliberationEnCours ? handleCancelDeliberation : undefined}
                      onNewDeliberation={handleNewDeliberation}
                      onClose={demanderFermeture}
                    />
                  </motion.div>
                )}

                {/* History View */}
                {viewState === 'history' && (
                  <motion.div
                    key="history"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="max-w-2xl mx-auto"
                  >
                    <h3 className="text-lg font-semibold text-text mb-4">
                      Historique des décisions
                    </h3>

                    {loadingHistory ? (
                      <div className="flex items-center justify-center py-12">
                        <Spinner taille="zone" className="text-text-muted" />
                      </div>
                    ) : (
                      <>
                        {/* B-873 / B-900 : la panne se dit ; une liste déjà
                            chargée reste visible sous l'alerte d'une action ratée. */}
                        {historyError && (
                          <Alerte
                            titre={decisions.length === 0 ? 'Historique indisponible' : 'Action impossible'}
                            action={decisions.length === 0 ? <Button variant="secondary" size="sm" onClick={handleShowHistory}>Réessayer</Button> : undefined}
                            className="mb-4"
                          >{historyError}</Alerte>
                        )}
                        {decisions.length === 0 && !historyError && (
                          <p className="text-center text-text-muted py-12">
                            Aucune décision enregistrée
                          </p>
                        )}
                        {decisions.length > 0 && (
                      <div className="space-y-3">
                        {decisions.map((decision) => (
                          <div
                            key={decision.id}
                            role="button"
                            tabIndex={0}
                            aria-label={decision.question}
                            className={cn(
                              'relative p-4 rounded-md',
                              'bg-surface-elevated border border-border',
                              'hover:border-accent-cyan/30 transition-colors',
                              'group cursor-pointer'
                            )}
                            onClick={() => handleViewDecision(decision.id)}
                            // B-876 : la carte s'ouvre aussi au clavier.
                            onKeyDown={(e) => {
                              if (e.target !== e.currentTarget) return;
                              if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleViewDecision(decision.id); }
                            }}
                          >
                            <p className="font-medium text-text mb-1 line-clamp-2 pr-8">
                              {decision.question}
                            </p>
                            <div className="flex items-center gap-3 text-sm text-text-muted">
                              <span>{new Date(decision.created_at).toLocaleDateString('fr-FR')}</span>
                              <span>•</span>
                              <span className={cn(
                                decision.confidence === 'high' && 'text-agent-green',
                                decision.confidence === 'medium' && 'text-warning',
                                decision.confidence === 'low' && 'text-error'
                              )}>
                                Confiance {LIBELLES_CONFIANCE[decision.confidence] ?? decision.confidence}
                              </span>
                            </div>
                            {decisionASupprimer === decision.id && (
                              <div
                                className="mt-3 flex flex-wrap items-center gap-2 rounded-sm border border-error/30 bg-[var(--color-error-tint)] px-3 py-2"
                                onClick={(e) => e.stopPropagation()}
                                onKeyDown={(e) => e.stopPropagation()}
                              >
                                <p className="flex-1 text-sm font-semibold text-error">Supprimer cette décision ? Cette action est irréversible.</p>
                                <Button variant="ghost" size="sm" onClick={() => setDecisionASupprimer(null)}>Conserver la décision</Button>
                                <Button variant="danger" size="sm" onClick={() => void handleDeleteDecision(decision.id)}>Supprimer définitivement</Button>
                              </div>
                            )}
                            {/* Delete button */}
                            <button
                              type="button"
                              onClick={(e) => { e.stopPropagation(); setDecisionASupprimer(decision.id); }}
                              onKeyDown={(e) => e.stopPropagation()}
                              className={cn(
                                'absolute top-3 right-3 p-2 rounded-md',
                                'text-text-muted hover:text-error',
                                'hover:bg-error/10 transition-colors',
                                'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100'
                              )}
                              title="Supprimer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                        )}
                      </>
                    )}
                  </motion.div>
                )}

                {/* Viewing Decision */}
                {viewState === 'viewing' && viewingDecision && (
                  <motion.div
                    key="viewing"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
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
              </>
            </div>
          </BoardDialogShell>
        </>
      )}
    </AnimatePresence>
  );
}
