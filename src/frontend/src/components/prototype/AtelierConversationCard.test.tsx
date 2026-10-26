import { fireEvent, render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
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

// B-1070 : lire la cascade réelle des jetons, y compris l'encre héritée
// en contraste élevé, plutôt que recopier des couleurs dans le test.
const css = readFileSync(join(__dirname, '../../styles/globals.css'), 'utf-8');
function jetons(selecteur: string): Record<string, string> {
  const debut = css.indexOf(`${selecteur} {`);
  if (debut === -1) throw new Error(`Thème introuvable : ${selecteur}`);
  const bloc = css.slice(debut, css.indexOf('\n}', debut));
  return Object.fromEntries([...bloc.matchAll(/--color-([\w-]+):\s*(#[\da-f]{6})/gi)]
    .map(([, nom, valeur]) => [nom, valeur]));
}

function luminance(hex: string): number {
  const rgb = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
}

describe('B-1070 : la confirmation Atelier reprend les jetons des boutons primaires', () => {
  it.each([
    ['review', 'Appliquer sur main'],
    ['review', 'Refuser'],
    ['merged', 'Annuler les changements'],
  ])('%s : %s garde le couple d’action commun', (status, action) => {
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={{ status: 'ready', data: { ...task, status }, error: null }}
      diffResource={{ status: 'ready', data: diff, error: null }}
      run={idleRun} target={task.id} actionPending={null} onRetry={vi.fn()}
      onRetryTask={vi.fn()} onStart={vi.fn()} onCancel={vi.fn()} onReset={vi.fn()}
      onMutate={vi.fn()} onOpenClassic={vi.fn()}
    />);
    fireEvent.click(screen.getByRole('button', { name: action }));
    const confirmer = screen.getByRole('button', { name: 'Confirmer l’action' });
    expect(confirmer).toHaveClass('bg-accent-fill', 'text-accent-ink');
    expect(confirmer).not.toHaveClass('bg-text', 'text-success-ink');
  });

  const clair = jetons('@theme');
  const sombre = { ...clair, ...jetons('[data-theme="dark"]') };
  const contrasteEleve = jetons('[data-high-contrast="true"]');
  it.each([
    ['clair', clair], ['sombre', sombre],
    ['contraste élevé sur clair', { ...clair, ...contrasteEleve }],
    ['contraste élevé sur sombre', { ...sombre, ...contrasteEleve }],
  ] as const)('%s : le contraste du couple commun atteint 4,5:1', (theme, couleurs) => {
    const [haut, bas] = [luminance(couleurs['accent-fill']), luminance(couleurs['accent-ink'])]
      .sort((a, b) => b - a);
    const ratio = (haut + 0.05) / (bas + 0.05);
    console.info(`${theme} : ${couleurs['accent-fill']} / ${couleurs['accent-ink']} = ${ratio.toFixed(4)}:1`);
    expect(ratio).toBeGreaterThanOrEqual(4.5);
  });
});

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

  it('B-1517 : la confirmation ne promet pas une exécution « locale » quand des extraits partent au modèle', () => {
    render(<AtelierWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      taskResource={null} diffResource={null} run={idleRun} target="new-mission"
      actionPending={null} onRetry={vi.fn()} onRetryTask={vi.fn()} onStart={vi.fn()}
      onCancel={vi.fn()} onReset={vi.fn()} onMutate={vi.fn()} onOpenClassic={vi.fn()}
    />);
    fireEvent.change(screen.getByLabelText('Mission Atelier'), { target: { value: 'Corriger le tri des factures.' } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la mission' }));
    const carte = screen.getByTestId('atelier-confirmation');
    expect(carte).not.toHaveTextContent(/exécution locale/i);
    expect(carte).toHaveTextContent('Les commandes s’exécutent sur ce poste ; des extraits du dépôt partent au modèle de chaque agente.');
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
