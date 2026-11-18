/**
 * B-1841 : le prévol dit « Branche inconnue » et « état inconnu », mais
 * « Préparer la mission » ne se bloque que pour un arbre explicitement sale
 * ou une branche renseignée et différente de main. Une valeur absente laisse
 * passer une mission dont on ne sait pas protéger le dépôt.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { AgentTaskResponse } from '../../services/api/agents';
import { AtelierWorkspaceCanvas } from './AtelierConversationCard';
import type { AtelierRunState, AtelierWorkspaceData } from './usePrototypeAtelierData';

const task = {
  id: 'task-1', title: 'Mission', description: '', status: 'review',
  branch_name: 'agent/task-1', diff_summary: '', files_changed: [],
  tokens_used: 0, cost_eur: 0, created_at: '2026-07-13T10:00:00Z', updated_at: '2026-07-13T10:05:00Z',
} as AgentTaskResponse;

const base: AtelierWorkspaceData = {
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

const idleRun = {
  status: 'idle', instruction: '', taskId: null, phase: '', branch: null,
  filesChanged: [], diffSummary: '', plan: '', explanation: '', tests: [], events: [], error: null,
  agents: {
    katia: { id: 'katia', status: 'waiting', content: '' },
    zezette: { id: 'zezette', status: 'waiting', content: '' },
  },
} as AtelierRunState;

function rendu(status: AtelierWorkspaceData['status']) {
  render(<AtelierWorkspaceCanvas
    resource={{ status: 'ready', data: { ...base, status }, error: null }}
    taskResource={null} diffResource={null} run={idleRun} target="new-mission"
    actionPending={null} onRetry={vi.fn()} onRetryTask={vi.fn()} onStart={vi.fn()}
    onCancel={vi.fn()} onReset={vi.fn()} onMutate={vi.fn()} onOpenClassic={vi.fn()}
  />);
}

describe('prévol Atelier : un état git non conclu bloque la mission (B-1841)', () => {
  it('une branche vide empêche de préparer la mission', () => {
    rendu({ ...base.status, current_branch: '' });
    expect(screen.getByTestId('atelier-preflight')).toHaveTextContent('Branche inconnue');
    expect(screen.getByRole('button', { name: 'Préparer la mission' })).toBeDisabled();
    expect(screen.getByRole('alert')).toHaveTextContent('La branche active est inconnue, main est requise.');
  });

  it('un dépôt ni propre ni sale empêche de préparer la mission', () => {
    rendu({ ...base.status, working_tree_clean: undefined });
    expect(screen.getByTestId('atelier-preflight')).toHaveTextContent('état inconnu');
    expect(screen.getByRole('button', { name: 'Préparer la mission' })).toBeDisabled();
    expect(screen.getByRole('alert')).toHaveTextContent('L’état du dépôt est inconnu.');
  });
});
