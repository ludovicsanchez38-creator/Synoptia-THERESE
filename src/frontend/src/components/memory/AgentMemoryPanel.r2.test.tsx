import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { AgentMemoryPanel } from './AgentMemoryPanel';
import { MemoryReceipt } from './MemoryReceipt';
import * as api from '../../services/api/memoryCards';
import { useDemoStore } from '../../stores/demoStore';
import { useAgentMemoryStore } from '../../stores/agentMemoryStore';

vi.mock('../../services/api/memoryCards', () => ({
  getMemoryCards: vi.fn(), getMemoryCard: vi.fn(), getMemoryScopes: vi.fn(),
  patchMemoryCard: vi.fn(), deleteMemoryCard: vi.fn(), releaseMemoryCard: vi.fn(),
  notifyMemoryChange: vi.fn(), listenMemoryChanges: () => () => {},
}));
const fiche = { id: 'c', kind: 'decision', title: 'Acompte décidé', content: 'Demande 30 %.', reason: 'Réserve le créneau.',
  subject: 'acompte', version: 1, protected: true, author: 'therese', last_author: 'utilisateur',
  scope: 'global', scope_name: 'Général', state: 'active', created_at: '2026-10-21T06:00:00Z', updated_at: '2026-10-21T06:01:00Z' } as api.MemoryCard;
beforeEach(() => {
  vi.clearAllMocks();
  useDemoStore.setState({ enabled: false });
  useAgentMemoryStore.setState({ selectedId: null, sourceMessageId: null });
  vi.mocked(api.getMemoryCards).mockResolvedValue({ items: [fiche], total: 1 });
  vi.mocked(api.getMemoryCard).mockResolvedValue(fiche);
  vi.mocked(api.getMemoryScopes).mockResolvedValue([]);
  vi.mocked(api.patchMemoryCard).mockResolvedValue({ ...fiche, version: 2 });
});

it('montre les cinq branches, les quatre types et la fiche avec sa raison', async () => {
  render(<AgentMemoryPanel />);
  expect(await screen.findByText('Acompte décidé')).toBeVisible();
  for (const label of ['Profil et consignes', 'Fiches et index', 'Journal des actions confirmées et envois', 'Brouillons en cours', 'Notes de rendez-vous']) expect(screen.getByRole('button', { name: new RegExp(label) })).toBeVisible();
  for (const label of ['Préférences', 'Faits clients et dossiers', 'Décisions et raisons', 'Corrections']) expect(screen.getByRole('option', { name: label })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Acompte décidé' }));
  expect(await screen.findByText('Réserve le créneau.')).toBeVisible();
  expect(screen.getByText('Corrigée par toi')).toBeVisible();
});

it('corrige avec la version lue puis exige une confirmation pour effacer', async () => {
  render(<AgentMemoryPanel />);
  fireEvent.click(await screen.findByRole('button', { name: 'Acompte décidé' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Modifier' }));
  fireEvent.change(screen.getByLabelText('Contenu'), { target: { value: 'Demande 40 %.' } });
  fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
  await waitFor(() => expect(api.patchMemoryCard).toHaveBeenCalledWith('c', expect.objectContaining({ version: 1, content: 'Demande 40 %.' })));
  fireEvent.click(screen.getByRole('button', { name: 'Effacer' }));
  expect(api.deleteMemoryCard).not.toHaveBeenCalled();
  expect(screen.getByRole('alertdialog')).toHaveTextContent('Effacer cette fiche ?');
  fireEvent.click(screen.getByRole('button', { name: 'Effacer définitivement' }));
  await waitFor(() => expect(api.deleteMemoryCard).toHaveBeenCalled());
});

it('distingue le vide de la panne et masque tout le contenu en démonstration', async () => {
  useDemoStore.setState({ enabled: true });
  render(<AgentMemoryPanel />);
  expect(await screen.findByText('Fiche de démonstration')).toBeVisible();
  expect(screen.queryByText('Acompte décidé')).not.toBeInTheDocument();
});

it('le reçu relit le titre en base et ne conserve pas le titre d’une fiche effacée', async () => {
  const vue = render(<MemoryReceipt id="c" />);
  expect(await screen.findByRole('button', { name: 'Noté : Acompte décidé' })).toBeVisible();
  vue.unmount();
  vi.mocked(api.getMemoryCard).mockRejectedValue({ status: 404 });
  render(<MemoryReceipt id="c" />);
  expect(await screen.findByText('Fiche effacée')).toBeVisible();
  expect(screen.queryByText('Acompte décidé')).not.toBeInTheDocument();
});
