/**
 * B-644 (persona Nadia, c4) : à 1024 px, le panneau Actions recouvre dix
 * commandes de la colonne principale qui restent focalisables, sans voile ni
 * `inert`, contrairement aux six panneaux de la coque (règle 0.48.1 :
 * usePanneauCouvrant + VoilePanneau).
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/actions', () => ({
  listAgents: vi.fn().mockResolvedValue([]),
  runAction: vi.fn(),
  listTasks: vi.fn().mockResolvedValue([]),
  getTask: vi.fn(),
  cancelTask: vi.fn(),
}));
const couvrant = vi.hoisted(() => ({ valeur: true }));
vi.mock('../../hooks/usePanneauCouvrant', async () => {
  const reel = await vi.importActual<typeof import('../../hooks/usePanneauCouvrant')>('../../hooks/usePanneauCouvrant');
  return { ...reel, usePanneauCouvrant: () => couvrant.valeur };
});

import { useActionsStore } from '../../stores/actionsStore';
import { ActionPanel } from './ActionPanel';

function Page() {
  return (
    <>
      <main data-testid="fond">
        <button type="button">Nouveau contact</button>
      </main>
      <ActionPanel />
    </>
  );
}

describe('B-644 : sous le seuil côte à côte, le panneau Actions isole ce qu’il recouvre', () => {
  beforeEach(() => {
    useActionsStore.setState({ isPanelOpen: true, activeTask: null, tasks: [], selectedAgent: null, agents: [] } as never);
  });

  it('un voile est posé et le fond devient inerte', async () => {
    couvrant.valeur = true;
    render(<Page />);
    expect(await screen.findByTestId('panneau-voile')).toBeInTheDocument();
    expect(screen.getByTestId('fond').hasAttribute('inert')).toBe(true);
  });

  it('côte à côte, ni voile ni isolation', () => {
    couvrant.valeur = false;
    render(<Page />);
    expect(screen.queryByTestId('panneau-voile')).toBeNull();
    expect(screen.getByTestId('fond').hasAttribute('inert')).toBe(false);
  });
});
