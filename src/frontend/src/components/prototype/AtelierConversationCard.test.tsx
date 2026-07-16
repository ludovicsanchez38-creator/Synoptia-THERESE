import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { AgentTaskResponse, DiffResponse } from '../../services/api/agents';
import { AtelierHistoryCard, AtelierWorkspaceCanvas } from './AtelierConversationCard';
import type { AtelierRunState, AtelierWorkspaceData } from './usePrototypeAtelierData';

const task: AgentTaskResponse = {
  id: 'task-1', title: 'Simplifier l’onboarding', description: 'Simplifier sans modifier les données.',
  status: 'review', branch_name: 'agent/task-1-onboarding', diff_summary: '1 file changed',
  files_changed: ['src/onboarding.ts'], tokens_used: 0, cost_eur: 0,
  created_at: '2026-07-13T10:00:00Z', updated_at: '2026-07-13T10:05:00Z',
};

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
  task_id: task.id, branch_name: task.branch_name, summary: task.diff_summary,
  files: [{ file_path: 'src/onboarding.ts', change_type: 'modified', diff_hunk: '-ancien\n+nouveau', additions: 1, deletions: 1 }],
  total_additions: 1, total_deletions: 1,
};

describe('Atelier 0.40 conversationnel', () => {
  it('affiche l’historique réel sans chiffres de démonstration', () => {
    const onOpenTask = vi.fn();
    render(<AtelierHistoryCard
      resource={{ status: 'ready', data: workspace, error: null }} run={idleRun}
      onRetry={vi.fn()} onOpenTask={onOpenTask} onNewMission={vi.fn()}
      onOpenCurrent={vi.fn()} onOpenClassic={vi.fn()}
    />);

    fireEvent.click(screen.getByText(task.title));
    expect(onOpenTask).toHaveBeenCalledWith(task.id);
    expect(screen.queryByText(/12 tests|0,18/)).not.toBeInTheDocument();
  });

  it('montre le périmètre puis exige une confirmation avant le lancement', () => {
    const onStart = vi.fn().mockResolvedValue(undefined);
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={null} diffResource={null} run={idleRun} target="new-mission"
      actionPending={null} onRetry={vi.fn()} onRetryTask={vi.fn()} onStart={onStart}
      onCancel={vi.fn()} onReset={vi.fn()} onMutate={vi.fn()} onOpenClassic={vi.fn()}
    />);

    expect(screen.getByTestId('atelier-preflight')).toHaveTextContent('/repo');
    expect(screen.getByTestId('atelier-new-form')).toHaveTextContent('Aucun email, devis, événement');
    fireEvent.change(screen.getByLabelText('Mission Atelier'), { target: { value: 'Simplifier l’onboarding sans modifier les données.' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la mission' }));
    expect(screen.getByTestId('atelier-confirmation')).toHaveTextContent('Simplifier l’onboarding sans modifier les données.');
    expect(screen.getByTestId('atelier-confirmation')).toHaveTextContent('/repo');
    expect(screen.getByLabelText('Mission Atelier')).toBeDisabled();
    expect(onStart).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et lancer' }));
    expect(onStart).toHaveBeenCalledWith('Simplifier l’onboarding sans modifier les données.');
  });

  it('réserve l’annulation d’une mission engagée à une confirmation dédiée', () => {
    const onCancel = vi.fn().mockResolvedValue(undefined);
    const runningRun: AtelierRunState = {
      ...idleRun,
      status: 'running',
      instruction: 'Simplifier le parcours sans toucher aux données.',
      phase: 'testing',
    };
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={null} diffResource={null} run={runningRun} target="current"
      actionPending={null} onRetry={vi.fn()} onRetryTask={vi.fn()} onStart={vi.fn()}
      onCancel={onCancel} onReset={vi.fn()} onMutate={vi.fn()} onOpenClassic={vi.fn()}
    />);

    fireEvent.click(screen.getByRole('button', { name: 'Annuler la mission' }));
    expect(screen.getByTestId('atelier-cancel-confirmation')).toBeInTheDocument();
    expect(onCancel).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer l’annulation' }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('bloque le lancement lorsque le dépôt contient des changements', () => {
    const dirty = { ...workspace, status: { ...workspace.status, working_tree_clean: false } };
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: dirty, error: null }}
      taskResource={null} diffResource={null} run={idleRun} target="new-mission"
      actionPending={null} onRetry={vi.fn()} onRetryTask={vi.fn()} onStart={vi.fn()}
      onCancel={vi.fn()} onReset={vi.fn()} onMutate={vi.fn()} onOpenClassic={vi.fn()}
    />);
    expect(screen.getByRole('button', { name: 'Préparer la mission' })).toBeDisabled();
    expect(screen.getByText(/Mission bloquée/)).toBeInTheDocument();
  });

  it('relit le diff et demande une seconde confirmation avant application', () => {
    const onMutate = vi.fn().mockResolvedValue({ ...task, status: 'merged' });
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={{ status: 'ready', data: task, error: null }}
      diffResource={{ status: 'ready', data: diff, error: null }}
      run={idleRun} target={task.id} actionPending={null} onRetry={vi.fn()}
      onRetryTask={vi.fn()} onStart={vi.fn()} onCancel={vi.fn()} onReset={vi.fn()}
      onMutate={onMutate} onOpenClassic={vi.fn()}
    />);

    expect(screen.getByTestId('atelier-diff')).toHaveTextContent('src/onboarding.ts');
    fireEvent.click(screen.getByRole('button', { name: 'Appliquer sur main' }));
    expect(onMutate).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer l’action' }));
    expect(onMutate).toHaveBeenCalledWith(task.id, 'approve');
  });

  it('reconstruit le plan, les tests et l’explication d’une mission enregistrée', () => {
    const persistedTask: AgentTaskResponse = {
      ...task,
      plan: 'Plan durable',
      test_results: ['3 tests passed'],
      explanation: 'Explication durable',
      agent_outputs: { katia: 'Cadrage final', zezette: 'Réalisation finale' },
      base_branch: 'main',
      commit_hash: 'abc123def456789',
      agent_model: '{"katia":"claude-test","zezette":"gpt-test"}',
    };
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={{ status: 'ready', data: persistedTask, error: null }}
      diffResource={{ status: 'ready', data: diff, error: null }}
      run={idleRun} target={task.id} actionPending={null} onRetry={vi.fn()}
      onRetryTask={vi.fn()} onStart={vi.fn()} onCancel={vi.fn()} onReset={vi.fn()}
      onMutate={vi.fn()} onOpenClassic={vi.fn()}
    />);

    expect(screen.getByText('Plan durable')).toBeInTheDocument();
    expect(screen.getByText('3 tests passed')).toBeInTheDocument();
    expect(screen.getByText('Explication durable')).toBeInTheDocument();
    expect(screen.getByText('Cadrage final')).toBeInTheDocument();
    expect(screen.getByText(/Commit : abc123def456/)).toBeInTheDocument();
  });
});
