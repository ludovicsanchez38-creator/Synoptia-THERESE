import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/board', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/api/board')>();
  return {
    ...actual,
    getBoardDecision: vi.fn(),
    listAdvisors: vi.fn(),
    listBoardDecisions: vi.fn(),
    streamDeliberation: vi.fn(),
  };
});

import {
  getBoardDecision,
  listAdvisors,
  listBoardDecisions,
  streamDeliberation,
  type AdvisorInfo,
  type BoardDecisionDetail,
  type BoardDeliberationChunk,
} from '../../services/api/board';
import { usePrototypeBoardData } from './usePrototypeBoardData';

const advisors: AdvisorInfo[] = [
  { role: 'analyst', name: "L'Analyste", emoji: '', color: '#22D3EE', personality: 'Données' },
  { role: 'strategist', name: 'Le Stratège', emoji: '', color: '#A855F7', personality: 'Vision' },
  { role: 'devil', name: "L'Avocat du Diable", emoji: '', color: '#EF4444', personality: 'Risques' },
  { role: 'pragmatic', name: 'Le Pragmatique', emoji: '', color: '#F59E0B', personality: 'Faisabilité' },
  { role: 'visionary', name: 'Le Visionnaire', emoji: '', color: '#E11D8D', personality: 'Innovation' },
];

const decision: BoardDecisionDetail = {
  id: 'decision-1',
  question: 'Faut-il lancer un pilote maintenant ?',
  context: 'Budget limité',
  opinions: [{ role: 'analyst', name: "L'Analyste", emoji: '', content: 'Commencer petit.' }],
  synthesis: {
    consensus_points: ['Tester'], divergence_points: [], recommendation: 'Lancer un pilote.',
    confidence: 'high', next_steps: ['Définir le périmètre'],
  },
  mode: 'cloud',
  created_at: '2026-07-13T10:00:00Z',
};

function consentCloud() {
  // Consentement v2 (revue 0.40.1, F4) : le Board exige SON accord dédié
  // (finalité llm, clé board) - un consentement LLM quelconque ne suffit plus.
  vi.mocked(window.localStorage.getItem).mockReturnValue(JSON.stringify({
    version: '2',
    grants: {
      'llm:board': {
        purpose: 'llm', provider: 'board', timestamp: '2026-07-13T10:00:00Z',
      },
    },
  }));
}

async function* chunks(values: BoardDeliberationChunk[]) {
  for (const value of values) yield value;
}

describe('usePrototypeBoardData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listAdvisors).mockResolvedValue(advisors);
    vi.mocked(listBoardDecisions).mockResolvedValue([{
      id: decision.id, question: decision.question, context: decision.context,
      recommendation: decision.synthesis.recommendation, confidence: 'high', mode: 'cloud',
      created_at: decision.created_at,
    }]);
    vi.mocked(getBoardDecision).mockResolvedValue(decision);
  });

  it('charge l’historique et ne lance rien à l’ouverture', async () => {
    const { result } = renderHook(() => usePrototypeBoardData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));
    expect(result.current.resource.data?.decisions[0].id).toBe('decision-1');
    expect(streamDeliberation).not.toHaveBeenCalled();
  });

  it('bloque une question courte et un cloud sans consentement', async () => {
    const { result } = renderHook(() => usePrototypeBoardData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    await act(async () => result.current.startDeliberation({ question: 'Court', mode: 'cloud' }));
    expect(result.current.run.status).toBe('error');
    expect(result.current.run.phase).toBe('Question incomplète');
    expect(streamDeliberation).not.toHaveBeenCalled();

    await act(async () => result.current.startDeliberation({ question: 'Une question suffisamment longue', mode: 'cloud' }));
    expect(result.current.run.phase).toBe('Consentement requis');
    expect(streamDeliberation).not.toHaveBeenCalled();
  });

  it('ne termine qu’après relecture de la décision sauvegardée', async () => {
    consentCloud();
    vi.mocked(streamDeliberation).mockImplementation(() => chunks([
      { type: 'advisor_start', role: 'analyst', name: "L'Analyste", provider: 'anthropic', content: '' },
      { type: 'advisor_chunk', role: 'analyst', content: 'Commencer petit.' },
      { type: 'advisor_done', role: 'analyst', content: 'Commencer petit.' },
      { type: 'synthesis_chunk', content: JSON.stringify(decision.synthesis) },
      { type: 'done', content: decision.id },
    ]));
    const { result } = renderHook(() => usePrototypeBoardData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    await act(async () => result.current.startDeliberation({ question: decision.question, mode: 'cloud' }));

    expect(getBoardDecision).toHaveBeenCalledWith(decision.id);
    expect(result.current.run.status).toBe('complete');
    expect(result.current.run.decisionId).toBe(decision.id);
    expect(result.current.decisionResource?.status).toBe('ready');
  });

  it('signale une sauvegarde non vérifiable au lieu d’annoncer un succès', async () => {
    consentCloud();
    vi.mocked(getBoardDecision).mockRejectedValue(new Error('404'));
    vi.mocked(streamDeliberation).mockImplementation(() => chunks([
      { type: 'synthesis_chunk', content: JSON.stringify(decision.synthesis) },
      { type: 'done', content: decision.id },
    ]));
    const { result } = renderHook(() => usePrototypeBoardData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    await act(async () => result.current.startDeliberation({ question: decision.question, mode: 'cloud' }));

    expect(result.current.run.status).toBe('persistence_error');
    expect(result.current.run.error).toMatch(/sauvegarde locale/i);
  });

  it('conserve une synthèse invalide en erreur et ignore le done suivant', async () => {
    consentCloud();
    vi.mocked(streamDeliberation).mockImplementation(() => chunks([
      { type: 'synthesis_chunk', content: 'pas du json' },
      { type: 'done', content: decision.id },
    ]));
    const { result } = renderHook(() => usePrototypeBoardData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    await act(async () => result.current.startDeliberation({ question: decision.question, mode: 'cloud' }));

    expect(result.current.run.status).toBe('error');
    expect(getBoardDecision).not.toHaveBeenCalled();
  });

  it('ignore un second lancement pendant un flux actif', async () => {
    consentCloud();
    let release: (() => void) | undefined;
    vi.mocked(streamDeliberation).mockImplementation(async function* () {
      yield { type: 'advisor_start', role: 'analyst', content: '' };
      await new Promise<void>((resolve) => { release = resolve; });
      yield { type: 'error', content: 'Arrêt de test' };
    });
    const { result } = renderHook(() => usePrototypeBoardData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    let first: Promise<void> | undefined;
    act(() => { first = result.current.startDeliberation({ question: decision.question, mode: 'cloud' }); });
    await waitFor(() => expect(streamDeliberation).toHaveBeenCalledTimes(1));
    act(() => { void result.current.startDeliberation({ question: 'Une autre question stratégique', mode: 'cloud' }); });
    expect(streamDeliberation).toHaveBeenCalledTimes(1);

    release?.();
    await act(async () => first);
  });

  it('laisse le flux actif quand le canevas Board est simplement masqué', async () => {
    consentCloud();
    let signal: AbortSignal | undefined;
    let release: (() => void) | undefined;
    vi.mocked(streamDeliberation).mockImplementation(async function* (_request, activeSignal) {
      signal = activeSignal;
      yield { type: 'advisor_start', role: 'analyst', content: '' };
      await new Promise<void>((resolve) => { release = resolve; });
      yield { type: 'error', content: 'Fin contrôlée du test' };
    });
    const { result, rerender } = renderHook(
      ({ enabled }) => usePrototypeBoardData(enabled),
      { initialProps: { enabled: true } },
    );
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    let deliberation: Promise<void> | undefined;
    act(() => { deliberation = result.current.startDeliberation({ question: decision.question, mode: 'cloud' }); });
    await waitFor(() => expect(result.current.run.status).toBe('running'));
    rerender({ enabled: false });

    expect(signal?.aborted).toBe(false);
    expect(result.current.run.status).toBe('running');
    release?.();
    await act(async () => deliberation);
  });
});
