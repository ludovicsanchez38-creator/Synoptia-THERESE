import { useCallback, useEffect, useRef, useState } from 'react';
import {
  getBoardDecision,
  listAdvisors,
  listBoardDecisions,
  streamDeliberation,
  type AdvisorInfo,
  type AdvisorRole,
  type BoardDecisionDetail,
  type BoardDecisionResponse,
  type BoardMode,
  type BoardRequest,
  type BoardSynthesis,
} from '../../services/api/board';
import type { ReadResource } from './usePrototypeReadData';
import { getCloudConsent } from '../../lib/consent';

export interface PrototypeAdvisorState {
  role: AdvisorRole;
  name: string;
  provider?: string;
  content: string;
  isRunning: boolean;
  isComplete: boolean;
}

export interface BoardWorkspaceData {
  decisions: BoardDecisionResponse[];
  advisors: AdvisorInfo[];
}

export type BoardRunStatus = 'idle' | 'running' | 'complete' | 'error' | 'persistence_error' | 'cancelled';

export interface BoardRunState {
  status: BoardRunStatus;
  question: string;
  context: string;
  mode: BoardMode;
  phase: string;
  isSearchingWeb: boolean;
  advisors: Record<string, PrototypeAdvisorState>;
  synthesis: BoardSynthesis | null;
  decisionId: string | null;
  error: string | null;
}

const idleRun: BoardRunState = {
  status: 'idle', question: '', context: '', mode: 'cloud', phase: '',
  isSearchingWeb: false, advisors: {}, synthesis: null, decisionId: null, error: null,
};

export function usePrototypeBoardData(enabled = true) {
  const [resource, setResource] = useState<ReadResource<BoardWorkspaceData>>({
    status: 'loading', data: null, error: null,
  });
  const [decisionResource, setDecisionResource] = useState<ReadResource<BoardDecisionDetail> | null>(null);
  const [run, setRun] = useState<BoardRunState>(idleRun);
  const historyRequestId = useRef(0);
  const detailRequestId = useRef(0);
  const selectedDecisionId = useRef<string | null>(null);
  const abortController = useRef<AbortController | null>(null);
  const running = useRef(false);

  const refresh = useCallback(async () => {
    const activeRequest = ++historyRequestId.current;
    setResource({ status: 'loading', data: null, error: null });
    try {
      const [decisions, advisors] = await Promise.all([
        listBoardDecisions(30),
        listAdvisors(),
      ]);
      if (activeRequest !== historyRequestId.current) return;
      setResource({ status: 'ready', data: { decisions, advisors }, error: null });
    } catch {
      if (activeRequest !== historyRequestId.current) return;
      setResource({
        status: 'error', data: null,
        error: 'Impossible de charger l’historique du Board pour le moment.',
      });
    }
  }, []);

  const openDecision = useCallback(async (decisionId: string) => {
    selectedDecisionId.current = decisionId;
    const activeRequest = ++detailRequestId.current;
    setDecisionResource({ status: 'loading', data: null, error: null });
    try {
      const decision = await getBoardDecision(decisionId);
      if (activeRequest !== detailRequestId.current) return;
      setDecisionResource({ status: 'ready', data: decision, error: null });
    } catch {
      if (activeRequest !== detailRequestId.current) return;
      setDecisionResource({
        status: 'error', data: null,
        error: 'Impossible de charger cette décision du Board.',
      });
    }
  }, []);

  const retryDecision = useCallback(async () => {
    if (selectedDecisionId.current) await openDecision(selectedDecisionId.current);
  }, [openDecision]);

  const startDeliberation = useCallback(async (request: BoardRequest) => {
    if (running.current) return;
    if (request.question.trim().length < 10) {
      setRun((current) => ({
        ...current,
        status: 'error',
        phase: 'Question incomplète',
        error: 'La question doit contenir au moins 10 caractères.',
      }));
      return;
    }
    if ((request.mode || 'cloud') === 'cloud' && !getCloudConsent()?.accepted) {
      setRun((current) => ({
        ...current,
        status: 'error',
        phase: 'Consentement requis',
        error: 'Le transfert cloud doit être confirmé avant de lancer le Board.',
      }));
      return;
    }
    running.current = true;
    const controller = new AbortController();
    abortController.current = controller;
    let receivedDone = false;
    setRun({
      ...idleRun,
      status: 'running',
      question: request.question.trim(),
      context: request.context?.trim() || '',
      mode: request.mode || 'cloud',
      phase: request.mode === 'sovereign' ? 'Démarrage du Board souverain' : 'Préparation de la recherche web',
    });

    try {
      for await (const chunk of streamDeliberation(request, controller.signal)) {
        if (controller.signal.aborted) break;
        if (chunk.type === 'web_search_start') {
          setRun((current) => ({ ...current, isSearchingWeb: true, phase: 'Recherche web en cours' }));
        } else if (chunk.type === 'web_search_done') {
          setRun((current) => ({ ...current, isSearchingWeb: false, phase: 'Consultation des conseillers' }));
        } else if (chunk.type === 'advisor_start' && chunk.role) {
          setRun((current) => ({
            ...current,
            phase: 'Consultation des conseillers',
            advisors: {
              ...current.advisors,
              [chunk.role!]: {
                role: chunk.role!, name: chunk.name || chunk.role!, provider: chunk.provider,
                content: '', isRunning: true, isComplete: false,
              },
            },
          }));
        } else if (chunk.type === 'advisor_chunk' && chunk.role) {
          setRun((current) => {
            const advisor = current.advisors[chunk.role!];
            if (!advisor) return current;
            return {
              ...current,
              advisors: {
                ...current.advisors,
                [chunk.role!]: { ...advisor, content: advisor.content + chunk.content },
              },
            };
          });
        } else if (chunk.type === 'advisor_done' && chunk.role) {
          setRun((current) => {
            const advisor = current.advisors[chunk.role!];
            if (!advisor) return current;
            return {
              ...current,
              advisors: {
                ...current.advisors,
                [chunk.role!]: { ...advisor, isRunning: false, isComplete: true },
              },
            };
          });
        } else if (chunk.type === 'synthesis_start') {
          setRun((current) => ({ ...current, phase: 'Synthèse en cours' }));
        } else if (chunk.type === 'synthesis_chunk') {
          try {
            const synthesis = JSON.parse(chunk.content) as BoardSynthesis;
            setRun((current) => ({ ...current, synthesis }));
          } catch {
            setRun((current) => ({ ...current, status: 'error', error: 'La synthèse reçue est illisible.' }));
            controller.abort();
            return;
          }
        } else if (chunk.type === 'done') {
          receivedDone = true;
          const decisionId = chunk.content || null;
          if (!decisionId) {
            setRun((current) => ({
              ...current,
              status: 'persistence_error',
              phase: 'Sauvegarde non vérifiable',
              error: 'Le Board n’a pas retourné d’identifiant de décision.',
            }));
            return;
          }
          try {
            selectedDecisionId.current = decisionId;
            const activeRequest = ++detailRequestId.current;
            const decision = await getBoardDecision(decisionId);
            if (activeRequest !== detailRequestId.current) return;
            setDecisionResource({ status: 'ready', data: decision, error: null });
            await refresh();
            setRun((current) => ({
              ...current,
              status: 'complete',
              phase: 'Délibération terminée et sauvegarde vérifiée',
              decisionId,
            }));
          } catch {
            setDecisionResource({
              status: 'error', data: null,
              error: 'La décision annoncée est introuvable dans l’historique local.',
            });
            setRun((current) => ({
              ...current,
              status: 'persistence_error',
              phase: 'Sauvegarde non vérifiable',
              decisionId,
              error: 'Le résultat a été reçu, mais sa sauvegarde locale n’a pas pu être vérifiée.',
            }));
          }
          return;
        } else if (chunk.type === 'error') {
          setRun((current) => ({ ...current, status: 'error', phase: 'Délibération interrompue', error: chunk.content || 'Le Board a rencontré une erreur.' }));
          return;
        }
      }

      if (controller.signal.aborted) {
        setRun((current) => ({ ...current, status: 'cancelled', phase: 'Délibération annulée', error: null }));
      } else if (!receivedDone) {
        setRun((current) => ({ ...current, status: 'error', phase: 'Flux interrompu', error: 'La délibération s’est interrompue avant sa sauvegarde.' }));
      }
    } catch (error) {
      if (controller.signal.aborted || (error instanceof DOMException && error.name === 'AbortError')) {
        setRun((current) => ({ ...current, status: 'cancelled', phase: 'Délibération annulée', error: null }));
      } else {
        setRun((current) => ({ ...current, status: 'error', phase: 'Délibération interrompue', error: 'Impossible de terminer la délibération.' }));
      }
    } finally {
      if (abortController.current === controller) abortController.current = null;
      running.current = false;
    }
  }, [refresh]);

  const cancelDeliberation = useCallback(() => {
    abortController.current?.abort();
  }, []);

  const resetRun = useCallback(() => {
    if (running.current) return;
    setRun({ ...idleRun });
  }, []);

  useEffect(() => {
    if (!enabled) return undefined;
    void refresh();
    return () => {
      historyRequestId.current += 1;
      detailRequestId.current += 1;
      abortController.current?.abort();
      abortController.current = null;
      running.current = false;
    };
  }, [enabled, refresh]);

  return {
    resource,
    decisionResource,
    run,
    refresh,
    openDecision,
    retryDecision,
    startDeliberation,
    cancelDeliberation,
    resetRun,
  };
}
