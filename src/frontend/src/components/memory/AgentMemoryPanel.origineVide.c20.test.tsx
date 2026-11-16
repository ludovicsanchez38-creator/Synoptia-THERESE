import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { AgentMemoryPanel } from './AgentMemoryPanel';
import { getMemoryCards } from '../../services/api/memoryCards';
import { useAgentMemoryStore } from '../../stores/agentMemoryStore';
import { useDemoStore } from '../../stores/demoStore';

vi.mock('../../services/api/memoryCards', () => ({
  getMemoryCards: vi.fn(), getMemoryCard: vi.fn(), getMemoryScopes: vi.fn().mockResolvedValue([]),
  patchMemoryCard: vi.fn(), deleteMemoryCard: vi.fn(), releaseMemoryCard: vi.fn(),
  notifyMemoryChange: vi.fn(), listenMemoryChanges: () => () => {},
}));

beforeEach(() => {
  vi.clearAllMocks();
  useDemoStore.setState({ enabled: false });
  useAgentMemoryStore.setState({ selectedId: null, sourceMessageId: null });
  vi.mocked(getMemoryCards).mockResolvedValue({ items: [], total: 0 });
});

it.each(['inconnue', 'documents'])('B-2021 : distingue une recherche par origine sans résultat de la mémoire vide (%s)', async (origine) => {
  render(<AgentMemoryPanel />);
  const accueilVide = 'Rien de noté pour le moment. Thérèse retiendra tes façons de travailler au fil de tes échanges.';
  const rechercheVide = 'Aucune fiche ne correspond à ta recherche.';
  expect(await screen.findByText(accueilVide)).toBeVisible();

  fireEvent.change(screen.getByLabelText('Origine'), { target: { value: origine } });
  await waitFor(() => expect(getMemoryCards).toHaveBeenLastCalledWith({
    query: '', state: 'active', offset: 0, limit: 25, provenance: origine,
  }));
  expect(await screen.findByText(rechercheVide)).toBeVisible();
  expect(screen.queryByText(accueilVide)).not.toBeInTheDocument();

  fireEvent.change(screen.getByLabelText('Origine'), { target: { value: '' } });
  expect(await screen.findByText(accueilVide)).toBeVisible();
  expect(screen.queryByText(rechercheVide)).not.toBeInTheDocument();
});
