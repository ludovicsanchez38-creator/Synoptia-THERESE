import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/api/agents')>();
  return {
    ...actual,
    approveTask: vi.fn(),
    cancelTask: vi.fn(),
    getAgentConfig: vi.fn(),
    getAgentStatus: vi.fn(),
    getAgentTask: vi.fn(),
    getTaskDiff: vi.fn(),
    listAgentTasks: vi.fn(),
    rejectTask: vi.fn(),
    rollbackTask: vi.fn(),
    streamAgentRequest: vi.fn(),
  };
});

import {
  cancelTask,
  getAgentConfig,
  getAgentStatus,
  getAgentTask,
  getTaskDiff,
  listAgentTasks,
  streamAgentRequest,
  type AgentStreamChunk,
  type AgentTaskResponse,
} from '../../services/api/agents';
import { usePrototypeAtelierData } from './usePrototypeAtelierData';

const task: AgentTaskResponse = {
  id: 'task-1', title: 'Simplifier l’onboarding', description: 'Simplifier l’onboarding sans toucher aux données.',
  status: 'review', branch_name: 'agent/task-1-onboarding', diff_summary: '1 file changed',
  files_changed: ['src/onboarding.ts'], tokens_used: 0, cost_eur: 0,
  created_at: '2026-07-13T10:00:00Z', updated_at: '2026-07-13T10:05:00Z',
};

const config = {
  katia_enabled: true, zezette_enabled: true,
  katia_model: 'claude-sonnet-4-6', zezette_model: 'claude-sonnet-4-6',
  source_path: '/repo', available_models: [],
};

const status = {
  git_available: true, repo_detected: true, repo_path: '/repo', current_branch: 'main',
  working_tree_clean: true, active_tasks: 0, katia_ready: true, zezette_ready: true,
};

const diff = {
  task_id: task.id, branch_name: task.branch_name, summary: task.diff_summary,
  files: [{ file_path: 'src/onboarding.ts', change_type: 'modified', diff_hunk: '-ancien\n+nouveau', additions: 1, deletions: 1 }],
  total_additions: 1, total_deletions: 1,
};

async function* chunks(values: AgentStreamChunk[]) {
  for (const value of values) yield value;
}

describe('usePrototypeAtelierData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listAgentTasks).mockResolvedValue({ tasks: [task], total: 1 });
    vi.mocked(getAgentConfig).mockResolvedValue(config);
    vi.mocked(getAgentStatus).mockResolvedValue(status);
    vi.mocked(getAgentTask).mockResolvedValue(task);
    vi.mocked(getTaskDiff).mockResolvedValue(diff);
  });

  it('charge l’historique et le préflight sans lancer de mission', async () => {
    const { result } = renderHook(() => usePrototypeAtelierData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    expect(result.current.resource.data?.tasks[0].id).toBe(task.id);
    expect(result.current.resource.data?.status.working_tree_clean).toBe(true);
    expect(streamAgentRequest).not.toHaveBeenCalled();
  });

  it('reconstruit la mission avec le plan, les tests et le diff réels', async () => {
    vi.mocked(streamAgentRequest).mockImplementation(() => chunks([
      { type: 'agent_start', agent: 'katia', task_id: task.id, phase: 'spec', content: 'Cadrage' },
      { type: 'handoff', agent: 'katia', task_id: task.id, phase: 'analysis', content: 'Plan réel transmis' },
      { type: 'agent_start', agent: 'zezette', task_id: task.id, phase: 'implementation', content: 'Implémentation' },
      { type: 'test_result', agent: 'zezette', task_id: task.id, content: 'Code retour : 0\n1 passed' },
      { type: 'review_ready', task_id: task.id, phase: 'review', branch: task.branch_name, files_changed: task.files_changed, diff_summary: task.diff_summary, content: '' },
      { type: 'done', task_id: task.id, phase: 'review', content: 'Prêt pour revue' },
    ]));
    const { result } = renderHook(() => usePrototypeAtelierData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    await act(async () => result.current.startMission('Simplifier l’onboarding sans toucher aux données.'));

    expect(result.current.run.status).toBe('review');
    expect(result.current.run.plan).toBe('Plan réel transmis');
    expect(result.current.run.tests).toEqual(['Code retour : 0\n1 passed']);
    expect(result.current.run.branch).toBe(task.branch_name);
    expect(result.current.diffResource?.status).toBe('ready');
    expect(getTaskDiff).toHaveBeenCalledWith(task.id);
  });

  it('annule aussi le processus backend avant de fermer le flux', async () => {
    const cancelledTask = { ...task, status: 'cancelled', branch_name: undefined };
    vi.mocked(getAgentTask).mockResolvedValue(cancelledTask);
    vi.mocked(cancelTask).mockResolvedValue({ status: 'cancelling' });
    vi.mocked(streamAgentRequest).mockImplementation(async function* (_message, _path, signal) {
      yield { type: 'agent_start', agent: 'katia', task_id: task.id, phase: 'spec', content: 'Cadrage' };
      await new Promise<void>((_resolve, reject) => {
        signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
      });
    });
    const { result } = renderHook(() => usePrototypeAtelierData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    let mission: Promise<void> | undefined;
    act(() => { mission = result.current.startMission('Annuler cette mission pendant son cadrage.'); });
    await waitFor(() => expect(result.current.run.taskId).toBe(task.id));
    await act(async () => result.current.cancelMission());
    await act(async () => mission);

    expect(cancelTask).toHaveBeenCalledWith(task.id);
    expect(result.current.run.status).toBe('cancelled');
  });
});
