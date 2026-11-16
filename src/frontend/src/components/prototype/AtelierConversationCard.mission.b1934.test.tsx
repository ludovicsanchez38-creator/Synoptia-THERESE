/**
 * B-1934 : le champ affiche « Mission à confier » mais son nom accessible est
 * « Mission Atelier ». Le diff et les résultats de tests sont peints hors
 * des jetons de thème.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { AgentTaskResponse, DiffResponse } from '../../services/api/agents';
import { AtelierWorkspaceCanvas } from './AtelierConversationCard';
import type { AtelierRunState, AtelierWorkspaceData } from './usePrototypeAtelierData';

const task = {
  id: 'task-1', title: 'Mission', description: '', status: 'review',
  branch_name: 'agent/task-1', diff_summary: '', files_changed: ['src/onboarding.ts'],
  tokens_used: 0, cost_eur: 0, created_at: '2026-07-13T10:00:00Z', updated_at: '2026-07-13T10:05:00Z',
  test_results: ['3 tests passed'],
} as AgentTaskResponse;

const workspace: AtelierWorkspaceData = {
  tasks: [task], total: 1,
  config: {
    katia_enabled: true, zezette_enabled: true,
    katia_model: 'claude-sonnet-4-6', zezette_model: 'claude-sonnet-4-6',
    source_path: '/repo', available_models: [],
  },
  status: {
    git_available: true, repo_detected: true, repo_path: '/repo', current_branch: 'main',
    working_tree_clean: true, active_tasks: 0, katia_ready: true, zezette_ready: true,
  },
};

const idleRun: AtelierRunState = {
  status: 'idle', instruction: '', taskId: null, phase: '', branch: null,
  filesChanged: [], diffSummary: '', plan: '', explanation: '', tests: [], events: [], error: null,
  agents: {
    katia: { id: 'katia', status: 'waiting', content: '' },
    zezette: { id: 'zezette', status: 'waiting', content: '' },
  },
};

const diff: DiffResponse = {
  task_id: task.id, branch_name: task.branch_name, summary: '',
  files: [{ file_path: 'src/onboarding.ts', change_type: 'modified', diff_hunk: '-ancien\n+nouveau', additions: 1, deletions: 1 }],
  total_additions: 1, total_deletions: 1,
};

const props = {
  actionPending: null, onRetry: vi.fn(), onRetryTask: vi.fn(), onStart: vi.fn(),
  onCancel: vi.fn(), onReset: vi.fn(), onMutate: vi.fn(), onOpenClassic: vi.fn(),
};

function suitLesJetons(fragment: string) {
  const bloc = screen.getByText((_, noeud) =>
    noeud?.tagName === 'PRE' && (noeud.textContent ?? '').includes(fragment));
  expect(bloc.className).not.toMatch(/#(?:0A0F1E|B6C7DA)/i);
  expect(bloc).toHaveClass('bg-surface-2', 'text-text');
}

describe('mission Atelier : nom accessible et jetons (B-1934)', () => {
  it('le champ s’appelle comme son libellé visible', () => {
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={null} diffResource={null} run={idleRun} target="new-mission" {...props}
    />);
    expect(screen.getByRole('textbox', { name: 'Mission à confier' })).toBeInTheDocument();
    expect(screen.queryByRole('textbox', { name: 'Mission Atelier' })).toBeNull();
  });

  it('le diff et les résultats de tests suivent les jetons de thème', () => {
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={{ status: 'ready', data: task, error: null }}
      diffResource={{ status: 'ready', data: diff, error: null }}
      run={idleRun} target={task.id} {...props}
    />);
    fireEvent.click(screen.getByRole('button', { name: /src\/onboarding\.ts/ }));
    suitLesJetons('+nouveau');
    suitLesJetons('3 tests passed');

    const run: AtelierRunState = { ...idleRun, status: 'done', instruction: 'Déjà lancée', tests: ['pytest ok'] };
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={null} diffResource={null} run={run} target="current" {...props}
    />);
    suitLesJetons('pytest ok');
  });
});
