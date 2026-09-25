/** B-1474 (recette P-146, lot 5, KO-12) : la catégorie s'affichait « STRATEGIE ». */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const agents = vi.hoisted(() => [
  { id: 'swot', name: 'Analyse SWOT', description: 'Forces et faiblesses', category: 'strategie', icon: 'Target', params: [] },
]);

vi.mock('../../services/api/actions', () => ({
  listAgents: vi.fn().mockResolvedValue(agents),
  runAction: vi.fn(),
  listTasks: vi.fn().mockResolvedValue([]),
  getTask: vi.fn(),
  cancelTask: vi.fn(),
}));

import { useActionsStore } from '../../stores/actionsStore';
import { ActionPanel } from './ActionPanel';

describe('B-1474 : libellé de catégorie accentué', () => {
  beforeEach(() => {
    useActionsStore.setState({ isPanelOpen: true, agents: agents as never, selectedAgent: null, activeTask: null, tasks: [] });
  });

  it('la catégorie stratégie se lit « Stratégie »', async () => {
    render(<ActionPanel />);
    expect(await screen.findByRole('heading', { level: 3, name: 'Stratégie' })).toBeTruthy();
  });
});
