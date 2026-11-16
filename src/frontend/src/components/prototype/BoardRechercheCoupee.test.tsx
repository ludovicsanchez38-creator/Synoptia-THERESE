import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ streamDeliberation: vi.fn() }));
vi.mock('../../services/api/board', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/board')>('../../services/api/board');
  return { ...reel, ...mocks };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true, grantCloudConsent: vi.fn() }));

import { BoardWorkspaceCanvas } from './BoardConversationCard';
import { usePrototypeBoardData } from './usePrototypeBoardData';

function ParcoursTemoin() {
  const board = usePrototypeBoardData(false);
  return <>
    <button onClick={() => void board.startDeliberation({ question: 'Faut-il lancer un pilote ?', mode: 'cloud' })}>
      Lancer le témoin
    </button>
    <BoardWorkspaceCanvas
      resource={{ status: 'ready', data: { decisions: [], advisors: [] }, error: null }}
      decisionResource={board.decisionResource} run={board.run} target="current"
      onRetry={vi.fn()} onRetryDecision={vi.fn()} onStart={board.startDeliberation}
      onCancel={board.cancelDeliberation} onReset={board.resetRun} onOpenClassic={vi.fn()}
    />
  </>;
}

describe('Recherche web du Board conversationnel', () => {
  it('garde le refus visible après le démarrage des conseillers', async () => {
    let terminer = () => {};
    mocks.streamDeliberation.mockImplementation(async function* () {
      yield { type: 'web_search_start', content: 'Recherche en cours' };
      yield { type: 'web_search_done', content: 'Recherche web coupée. Réactive-la dans Paramètres > Services.' };
      yield { type: 'advisor_start', role: 'analyst', name: "L'Analyste", content: '' };
      yield { type: 'advisor_chunk', role: 'analyst', content: 'Avis témoin' };
      await new Promise<void>((resolve) => { terminer = resolve; });
    });

    render(<ParcoursTemoin />);
    fireEvent.click(screen.getByRole('button', { name: 'Lancer le témoin' }));

    expect(await screen.findByText('Avis témoin')).toBeInTheDocument();
    expect(screen.getByText('Recherche web coupée. Réactive-la dans Paramètres > Services.')).toBeInTheDocument();
    await act(async () => { terminer(); });
  });
});
