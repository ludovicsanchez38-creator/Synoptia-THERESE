import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
const api = vi.hoisted(() => ({ request: vi.fn(), initializeAuth: vi.fn().mockResolvedValue(undefined) }));
vi.mock('../services/api/core', () => api);
import { RepriseDonnees } from './RepriseDonnees';
const copie = { id: '20261027T080000Z-v0.81.1', date: '2026-10-27T08:00:00+00:00', version: '0.81.1' };
beforeEach(() => { vi.clearAllMocks(); api.request.mockResolvedValue({ copies: [copie] }); });
it('affiche date et version, attend la confirmation, puis propose de redémarrer', async () => {
  const relancer = vi.fn();
  render(<RepriseDonnees onRestart={relancer} />);
  expect(await screen.findByText(/0.81.1/)).toHaveTextContent(/27\/10\/2026/);
  fireEvent.click(screen.getByRole('button', { name: /Restaurer cette copie/ }));
  expect(api.request).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
  expect(screen.queryByRole('dialog')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: /Restaurer cette copie/ }));
  api.request.mockResolvedValue({ base_mise_de_cote: '/profil/backups/reprises/abri' });
  fireEvent.click(screen.getByRole('button', { name: 'Confirmer la restauration' }));
  await waitFor(() => expect(api.request).toHaveBeenLastCalledWith('/api/reprise/restaurer', expect.objectContaining({
    method: 'POST', body: JSON.stringify({ copie: copie.id, confirmer: true }), timeoutMs: 0,
  })));
  expect(await screen.findByText(/abri/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Redémarrer le moteur' }));
  expect(relancer).toHaveBeenCalledTimes(1);
});
it('dit quand aucune copie n’existe et permet de réessayer le démarrage', async () => {
  api.request.mockResolvedValue({ copies: [] });
  render(<RepriseDonnees onRestart={vi.fn()} />);
  expect(await screen.findByText(/Aucune copie automatique/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Réessayer le démarrage' })).toBeInTheDocument();
});
it('garde les copies disponibles après un échec de restauration', async () => {
  render(<RepriseDonnees onRestart={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: /Restaurer cette copie/ }));
  api.request.mockRejectedValue(new Error('Copie illisible'));
  fireEvent.click(screen.getByRole('button', { name: 'Confirmer la restauration' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Copie illisible');
  expect(screen.getByRole('button', { name: /Restaurer cette copie/ })).toBeEnabled();
});
