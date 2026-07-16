import { useCallback, useEffect, useRef, useState } from 'react';
import {
  approveTask,
  cancelTask,
  getAgentConfig,
  getAgentStatus,
  getAgentTask,
  getTaskDiff,
  listAgentTasks,
  rejectTask,
  rollbackTask,
  streamAgentRequest,
  type AgentConfigResponse,
  type AgentId,
  type AgentStatusResponse,
  type AgentStreamChunk,
  type AgentTaskResponse,
  type DiffResponse,
  type MissionPhase,
} from '../../services/api/agents';
import type { ReadResource } from './usePrototypeReadData';

export interface AtelierWorkspaceData {
  tasks: AgentTaskResponse[];
  total: number;
  config: AgentConfigResponse;
  status: AgentStatusResponse;
}

export interface AtelierAgentState {
  id: AgentId;
  status: 'waiting' | 'running' | 'done';
  content: string;
}

export interface AtelierRunEvent {
  id: number;
  type: AgentStreamChunk['type'];
  agent?: AgentId;
  label: string;
  content: string;
}

export type AtelierRunStatus =
  | 'idle'
  | 'running'
  | 'review'
  | 'done'
  | 'cancelled'
  | 'error'
  | 'persistence_error';

export interface AtelierRunState {
  status: AtelierRunStatus;
  instruction: string;
  taskId: string | null;
  phase: MissionPhase | 'cancelled' | 'error' | '';
  branch: string | null;
  filesChanged: string[];
  diffSummary: string;
  plan: string;
  explanation: string;
  tests: string[];
  agents: Record<AgentId, AtelierAgentState>;
  events: AtelierRunEvent[];
  error: string | null;
}

const idleRun: AtelierRunState = {
  status: 'idle',
  instruction: '',
  taskId: null,
  phase: '',
  branch: null,
  filesChanged: [],
  diffSummary: '',
  plan: '',
  explanation: '',
  tests: [],
  agents: {
    katia: { id: 'katia', status: 'waiting', content: '' },
    zezette: { id: 'zezette', status: 'waiting', content: '' },
  },
  events: [],
  error: null,
};

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

function isActiveStatus(status: string): boolean {
  return status === 'pending' || status === 'in_progress';
}

async function readTaskAfterStream(taskId: string): Promise<AgentTaskResponse> {
  let task = await getAgentTask(taskId);
  for (let attempt = 0; attempt < 15 && isActiveStatus(task.status); attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 120));
    task = await getAgentTask(taskId);
  }
  return task;
}

export function usePrototypeAtelierData(enabled = true) {
  const [resource, setResource] = useState<ReadResource<AtelierWorkspaceData>>({
    status: 'loading', data: null, error: null,
  });
  const [taskResource, setTaskResource] = useState<ReadResource<AgentTaskResponse> | null>(null);
  const [diffResource, setDiffResource] = useState<ReadResource<DiffResponse> | null>(null);
  const [run, setRun] = useState<AtelierRunState>(idleRun);
  const [actionPending, setActionPending] = useState<'approve' | 'reject' | 'rollback' | null>(null);
  const historyRequestId = useRef(0);
  const detailRequestId = useRef(0);
  const selectedTaskId = useRef<string | null>(null);
  const abortController = useRef<AbortController | null>(null);
  const running = useRef(false);
  const runningTaskId = useRef<string | null>(null);
  const cancelRequested = useRef(false);
  const actionLocked = useRef(false);
  const eventCounter = useRef(0);

  const refresh = useCallback(async () => {
    const activeRequest = ++historyRequestId.current;
    setResource({ status: 'loading', data: null, error: null });
    try {
      const [taskList, config, status] = await Promise.all([
        listAgentTasks(30),
        getAgentConfig(),
        getAgentStatus(),
      ]);
      if (activeRequest !== historyRequestId.current) return;
      setResource({
        status: 'ready',
        data: { tasks: taskList.tasks, total: taskList.total, config, status },
        error: null,
      });
    } catch {
      if (activeRequest !== historyRequestId.current) return;
      setResource({
        status: 'error', data: null,
        error: 'Impossible de charger l’Atelier local pour le moment.',
      });
    }
  }, []);

  const loadTask = useCallback(async (taskId: string, activeRequest: number) => {
    const task = await getAgentTask(taskId);
    if (activeRequest !== detailRequestId.current) return null;
    setTaskResource({ status: 'ready', data: task, error: null });

    if (task.status === 'review' && task.branch_name) {
      setDiffResource({ status: 'loading', data: null, error: null });
      try {
        const diff = await getTaskDiff(taskId);
        if (activeRequest !== detailRequestId.current) return task;
        setDiffResource({ status: 'ready', data: diff, error: null });
      } catch {
        if (activeRequest !== detailRequestId.current) return task;
        setDiffResource({
          status: 'error', data: null,
          error: 'La mission existe, mais son diff Git n’est pas lisible.',
        });
      }
    } else {
      setDiffResource(null);
    }
    return task;
  }, []);

  const openTask = useCallback(async (taskId: string) => {
    selectedTaskId.current = taskId;
    const activeRequest = ++detailRequestId.current;
    setTaskResource({ status: 'loading', data: null, error: null });
    setDiffResource(null);
    try {
      await loadTask(taskId, activeRequest);
    } catch {
      if (activeRequest !== detailRequestId.current) return;
      setTaskResource({
        status: 'error', data: null,
        error: 'Impossible de charger cette mission de l’Atelier.',
      });
    }
  }, [loadTask]);

  const retryTask = useCallback(async () => {
    if (selectedTaskId.current) await openTask(selectedTaskId.current);
  }, [openTask]);

  const addEvent = useCallback((chunk: AgentStreamChunk, label: string) => {
    if (!chunk.content && chunk.type === 'agent_chunk') return;
    const id = ++eventCounter.current;
    setRun((current) => ({
      ...current,
      events: [...current.events, {
        id,
        type: chunk.type,
        agent: chunk.agent,
        label,
        content: chunk.content,
      }],
    }));
  }, []);

  const verifyTerminalTask = useCallback(async (taskId: string) => {
    const task = await readTaskAfterStream(taskId);
    selectedTaskId.current = taskId;
    const activeRequest = ++detailRequestId.current;
    setTaskResource({ status: 'ready', data: task, error: null });

    if (task.status === 'review' && task.branch_name) {
      try {
        const diff = await getTaskDiff(taskId);
        if (activeRequest !== detailRequestId.current) return task;
        setDiffResource({ status: 'ready', data: diff, error: null });
        setRun((current) => ({
          ...current,
          status: 'review',
          phase: 'review',
          branch: task.branch_name || current.branch,
          filesChanged: task.files_changed || current.filesChanged,
          diffSummary: task.diff_summary || current.diffSummary,
          error: null,
        }));
      } catch {
        setDiffResource({
          status: 'error', data: null,
          error: 'La mission est en revue, mais son diff Git n’a pas pu être relu.',
        });
        setRun((current) => ({
          ...current,
          status: 'persistence_error',
          phase: 'error',
          error: 'La mission est enregistrée, mais sa revue Git est indisponible.',
        }));
      }
    } else if (task.status === 'done' || task.status === 'merged' || task.status === 'rejected') {
      setDiffResource(null);
      setRun((current) => ({ ...current, status: 'done', phase: 'done', error: null }));
    } else if (task.status === 'cancelled') {
      setDiffResource(null);
      setRun((current) => ({ ...current, status: 'cancelled', phase: 'cancelled', error: null }));
    } else if (task.status === 'error') {
      setRun((current) => ({
        ...current, status: 'error', phase: 'error',
        error: task.error || current.error || 'La mission a échoué.',
      }));
    } else {
      setRun((current) => ({
        ...current, status: 'persistence_error', phase: 'error',
        error: `Le flux est terminé, mais la mission est encore en statut « ${task.status} ».`,
      }));
    }
    return task;
  }, []);

  const startMission = useCallback(async (instruction: string) => {
    const normalized = instruction.trim();
    if (running.current) return;
    if (normalized.length < 15) {
      setRun((current) => ({
        ...current, status: 'error', phase: 'error',
        error: 'Décris la mission en au moins 15 caractères.',
      }));
      return;
    }

    running.current = true;
    cancelRequested.current = false;
    runningTaskId.current = null;
    eventCounter.current = 0;
    const controller = new AbortController();
    abortController.current = controller;
    setTaskResource(null);
    setDiffResource(null);
    setRun({ ...idleRun, status: 'running', instruction: normalized, phase: 'spec' });

    try {
      for await (const chunk of streamAgentRequest(normalized, undefined, controller.signal)) {
        if (chunk.task_id) {
          runningTaskId.current = chunk.task_id;
          setRun((current) => ({ ...current, taskId: chunk.task_id || current.taskId }));
        }
        if (chunk.phase) setRun((current) => ({ ...current, phase: chunk.phase || current.phase }));

        if (chunk.type === 'agent_start' && chunk.agent) {
          setRun((current) => ({
            ...current,
            agents: {
              ...current.agents,
              [chunk.agent!]: { ...current.agents[chunk.agent!], status: 'running' },
            },
          }));
          addEvent(chunk, chunk.agent === 'katia' ? 'Katia commence' : 'Zézette commence');
        } else if (chunk.type === 'agent_chunk' && chunk.agent) {
          setRun((current) => ({
            ...current,
            agents: {
              ...current.agents,
              [chunk.agent!]: {
                ...current.agents[chunk.agent!],
                content: current.agents[chunk.agent!].content + chunk.content,
              },
            },
          }));
        } else if (chunk.type === 'agent_done' && chunk.agent) {
          setRun((current) => ({
            ...current,
            agents: {
              ...current.agents,
              [chunk.agent!]: { ...current.agents[chunk.agent!], status: 'done' },
            },
          }));
          addEvent(chunk, chunk.agent === 'katia' ? 'Katia a terminé' : 'Zézette a terminé');
        } else if (chunk.type === 'handoff') {
          setRun((current) => ({ ...current, plan: chunk.content }));
          addEvent(chunk, 'Plan transmis à Zézette');
        } else if (chunk.type === 'tool_use') {
          addEvent(chunk, `Outil utilisé : ${chunk.tool_name || 'outil local'}`);
        } else if (chunk.type === 'test_result') {
          setRun((current) => ({
            ...current, phase: 'testing', tests: [...current.tests, chunk.content],
          }));
          addEvent(chunk, 'Résultat de commande de vérification');
        } else if (chunk.type === 'review_ready') {
          setRun((current) => ({
            ...current,
            phase: 'review',
            branch: chunk.branch || null,
            filesChanged: chunk.files_changed || [],
            diffSummary: chunk.diff_summary || '',
          }));
          addEvent(chunk, 'Revue prête');
        } else if (chunk.type === 'explanation') {
          setRun((current) => ({
            ...current, explanation: current.explanation + chunk.content,
          }));
        } else if (chunk.type === 'error') {
          setRun((current) => ({
            ...current, status: 'error', phase: 'error',
            error: chunk.content || 'La mission a échoué.',
          }));
          addEvent(chunk, 'Mission interrompue');
        }
      }

      if (runningTaskId.current) {
        await verifyTerminalTask(runningTaskId.current);
      } else if (cancelRequested.current || controller.signal.aborted) {
        setRun((current) => ({ ...current, status: 'cancelled', phase: 'cancelled', error: null }));
      } else {
        setRun((current) => ({
          ...current, status: 'error', phase: 'error',
          error: current.error || 'Le backend n’a retourné aucun identifiant de mission.',
        }));
      }
    } catch (error) {
      if (runningTaskId.current) {
        try {
          await verifyTerminalTask(runningTaskId.current);
        } catch {
          setRun((current) => ({
            ...current,
            status: cancelRequested.current ? 'cancelled' : 'persistence_error',
            phase: cancelRequested.current ? 'cancelled' : 'error',
            error: cancelRequested.current ? null : 'Le statut final de la mission n’a pas pu être vérifié.',
          }));
        }
      } else if (cancelRequested.current || controller.signal.aborted) {
        setRun((current) => ({ ...current, status: 'cancelled', phase: 'cancelled', error: null }));
      } else {
        setRun((current) => ({
          ...current, status: 'error', phase: 'error',
          error: errorMessage(error, 'Impossible de lancer la mission.'),
        }));
      }
    } finally {
      if (abortController.current === controller) abortController.current = null;
      running.current = false;
      runningTaskId.current = null;
      cancelRequested.current = false;
      await refresh();
    }
  }, [addEvent, refresh, verifyTerminalTask]);

  const cancelMission = useCallback(async () => {
    if (!running.current) return;
    cancelRequested.current = true;
    const taskId = runningTaskId.current;
    if (taskId) {
      try {
        await cancelTask(taskId);
      } catch (error) {
        setRun((current) => ({
          ...current, error: errorMessage(error, 'Le backend n’a pas confirmé l’annulation.'),
        }));
      }
    }
    abortController.current?.abort();
  }, []);

  const mutateTask = useCallback(async (
    taskId: string,
    action: 'approve' | 'reject' | 'rollback',
  ) => {
    if (actionLocked.current) return;
    actionLocked.current = true;
    setActionPending(action);
    try {
      if (action === 'approve') await approveTask(taskId);
      else if (action === 'reject') await rejectTask(taskId);
      else await rollbackTask(taskId);

      const task = await getAgentTask(taskId);
      const expectedStatus = action === 'approve' ? 'merged' : 'rejected';
      if (task.status !== expectedStatus) {
        throw new Error(`Le backend annonce encore le statut « ${task.status} ».`);
      }
      selectedTaskId.current = taskId;
      setTaskResource({ status: 'ready', data: task, error: null });
      setDiffResource(null);
      await refresh();
      return task;
    } catch (error) {
      setTaskResource((current) => current?.status === 'ready' ? {
        status: 'error', data: null,
        error: errorMessage(error, 'L’action n’a pas pu être vérifiée.'),
      } : current);
      throw error;
    } finally {
      actionLocked.current = false;
      setActionPending(null);
    }
  }, [refresh]);

  const resetRun = useCallback(() => {
    if (running.current) return;
    setRun({ ...idleRun });
    setTaskResource(null);
    setDiffResource(null);
    selectedTaskId.current = null;
  }, []);

  useEffect(() => {
    if (enabled) void refresh();
  }, [enabled, refresh]);

  useEffect(() => () => {
      historyRequestId.current += 1;
      detailRequestId.current += 1;
      if (running.current && runningTaskId.current) {
        void cancelTask(runningTaskId.current).catch(() => undefined);
      }
      abortController.current?.abort();
      abortController.current = null;
  }, []);

  return {
    resource,
    taskResource,
    diffResource,
    run,
    actionPending,
    refresh,
    openTask,
    retryTask,
    startMission,
    cancelMission,
    mutateTask,
    resetRun,
  };
}
