import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AdvisorInfo, BoardDecisionDetail } from '../../services/api/board';
import { BoardHistoryCard, BoardWorkspaceCanvas } from './BoardConversationCard';
import type { BoardRunState, BoardWorkspaceData } from './usePrototypeBoardData';

const advisors: AdvisorInfo[] = [
  { role: 'analyst', name: "L'Analyste", emoji: '', color: '#22D3EE', personality: 'Données' },
  { role: 'strategist', name: 'Le Stratège', emoji: '', color: '#A855F7', personality: 'Vision' },
  { role: 'devil', name: "L'Avocat du Diable", emoji: '', color: '#EF4444', personality: 'Risques' },
  { role: 'pragmatic', name: 'Le Pragmatique', emoji: '', color: '#F59E0B', personality: 'Faisabilité' },
  { role: 'visionary', name: 'Le Visionnaire', emoji: '', color: '#E11D8D', personality: 'Innovation' },
];

const synthesis = {
  consensus_points: ['Tester'], divergence_points: ['Budget'], recommendation: 'Lancer un pilote réel.',
  confidence: 'high' as const, next_steps: ['Définir le périmètre'],
};

const decision: BoardDecisionDetail = {
  id: 'decision-1', question: 'Faut-il lancer un pilote maintenant ?', context: 'Budget limité',
  opinions: [{ role: 'analyst', name: "L'Analyste", emoji: '', content: 'Mesurer avant extension.' }],
  synthesis, mode: 'sovereign', created_at: '2026-07-13T10:00:00Z',
};

const idleRun: BoardRunState = {
  status: 'idle', question: '', context: '', mode: 'cloud', phase: '', isSearchingWeb: false,
  advisors: {}, synthesis: null, decisionId: null, error: null,
};

const workspace: BoardWorkspaceData = {
  advisors,
  decisions: [{
    id: decision.id, question: decision.question, context: decision.context,
    recommendation: synthesis.recommendation, confidence: 'high', mode: 'sovereign',
    created_at: decision.created_at,
  }],
};

describe('Board 0.40 conversationnel', () => {
  beforeEach(() => vi.clearAllMocks());

  it('affiche l’historique réel et ouvre la décision par son identifiant', () => {
    const onOpenDecision = vi.fn();
    render(<BoardHistoryCard
      resource={{ status: 'ready', data: workspace, error: null }} run={idleRun}
      onRetry={vi.fn()} onOpenDecision={onOpenDecision} onNewBoard={vi.fn()}
      onOpenCurrent={vi.fn()} onOpenClassic={vi.fn()}
    />);

    expect(screen.getByText(decision.question)).toBeInTheDocument();
    expect(screen.getByText(synthesis.recommendation)).toBeInTheDocument();
    expect(screen.queryByText(/ÉCLORE/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText(decision.question));
    expect(onOpenDecision).toHaveBeenCalledWith(decision.id);
  });

  it('demande une confirmation explicite et trace le consentement avant le cloud', () => {
    const onStart = vi.fn().mockResolvedValue(undefined);
    render(<BoardWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }} decisionResource={null}
      run={idleRun} target="new-board" onRetry={vi.fn()} onRetryDecision={vi.fn()}
      onStart={onStart} onCancel={vi.fn()} onReset={vi.fn()} onOpenClassic={vi.fn()}
    />);

    fireEvent.change(screen.getByLabelText('Question stratégique'), {
      target: { value: 'Faut-il lancer un pilote maintenant ?' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la délibération' }));
    expect(screen.getByTestId('board-confirmation')).toHaveTextContent('Jusqu’à six appels LLM');
    expect(onStart).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et lancer' }));
    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      'therese-cloud-consent', expect.stringContaining('"accepted":true'),
    );
    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({ mode: 'cloud' }));
  });

  it('rend le détail sauvegardé sans inventer les providers historiques', () => {
    render(<BoardWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      decisionResource={{ status: 'ready', data: decision, error: null }}
      run={idleRun} target={decision.id} onRetry={vi.fn()} onRetryDecision={vi.fn()}
      onStart={vi.fn()} onCancel={vi.fn()} onReset={vi.fn()} onOpenClassic={vi.fn()}
    />);

    expect(screen.getByTestId('board-decision-detail')).toHaveTextContent('Mesurer avant extension.');
    expect(screen.getByTestId('board-decision-detail')).toHaveTextContent('Lancer un pilote réel.');
    expect(screen.queryByText(/anthropic|openai|gemini/i)).not.toBeInTheDocument();
  });
});
