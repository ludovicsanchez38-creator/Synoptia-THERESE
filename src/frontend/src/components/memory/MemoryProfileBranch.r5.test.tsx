import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { MemoryProfileBranch } from './MemoryProfileBranch';
import * as api from '../../services/api';
import { useDemoStore } from '../../stores/demoStore';
vi.mock('../../services/api', async original => ({
  ...(await original<typeof import('../../services/api')>()),
  getProfile: vi.fn().mockResolvedValue({ name: 'Personne Fictive', display_name: 'Personne Fictive', context: 'Contexte professionnel' }),
  setProfile: vi.fn().mockResolvedValue({ name: 'Personne Corrigée' }),
  getThereseMd: vi.fn().mockResolvedValue({ content: 'Consignes fictives', path: '/fictif/THERESE.md' }),
  getApiKeysWithCorrupted: vi.fn(), getLLMConfig: vi.fn(), getOllamaStatus: vi.fn(), getWebSearchStatus: vi.fn(),
}));
beforeEach(() => { vi.clearAllMocks(); useDemoStore.setState({ enabled: false }); });
it('ouvre le vrai éditeur du profil et de THERESE.md sans lecture de service distant', async () => {
  render(<MemoryProfileBranch />);
  expect(api.getProfile).not.toHaveBeenCalled();
  const ouvrir = screen.getByRole('button', { name: 'Modifier mon profil et mes consignes' });
  ouvrir.focus(); fireEvent.click(ouvrir);
  await waitFor(() => expect(screen.getByDisplayValue('Personne Fictive')).toBeVisible());
  expect(api.getApiKeysWithCorrupted).not.toHaveBeenCalled();
  expect(api.getLLMConfig).not.toHaveBeenCalled();
  expect(api.getOllamaStatus).not.toHaveBeenCalled();
  expect(api.getWebSearchStatus).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Voir THERESE.md' }));
  await waitFor(() => expect(screen.getByDisplayValue('Consignes fictives')).toBeVisible());
  fireEvent.click(within(screen.getByRole('dialog', { name: 'Aperçu THERESE.md' })).getByRole('button', { name: 'Fermer' }));
  fireEvent.click(screen.getByRole('button', { name: 'Fermer les paramètres' }));
  await waitFor(() => expect(ouvrir).toHaveFocus());
});
it('masque le profil et interdit son ouverture en démonstration', () => {
  useDemoStore.setState({ enabled: true });
  render(<MemoryProfileBranch />);
  expect(screen.getByRole('button', { name: 'Modifier mon profil et mes consignes' })).toBeDisabled();
  expect(api.getProfile).not.toHaveBeenCalled();
  expect(screen.queryByText('Personne Fictive')).not.toBeInTheDocument();
});
