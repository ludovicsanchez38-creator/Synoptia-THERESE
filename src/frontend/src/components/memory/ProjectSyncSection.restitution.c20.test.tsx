import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ etatSync: vi.fn(), reprendreIndexSync: vi.fn() }));
vi.mock('../../services/api', () => api);
import { ProjectSyncSection } from './ProjectSyncSection';

const etat = (attente: boolean) => ({
  racine: '/dossier', generation: 1, dernier_plan: null, run: null,
  restitution_en_attente: attente,
});

beforeEach(() => {
  vi.resetAllMocks();
  api.etatSync.mockResolvedValue(etat(true));
});

it('garde la restitution visible tant que la reprise échoue, puis rend la synchronisation', async () => {
  api.reprendreIndexSync.mockResolvedValueOnce(etat(true)).mockResolvedValueOnce(etat(false));
  render(<ProjectSyncSection projectId="dossier" />);
  const reprendre = await screen.findByRole('button', { name: 'Réessayer la restitution' });
  expect(screen.getByRole('alert')).toHaveTextContent('Les documents de ce dossier ne sont pas encore tous consultables.');
  expect(screen.getByRole('button', { name: /Préparer la synchronisation/ })).toBeDisabled();
  fireEvent.click(reprendre);
  await waitFor(() => expect(api.reprendreIndexSync).toHaveBeenCalledWith('dossier'));
  await waitFor(() => expect(reprendre).toBeEnabled());
  expect(screen.getByRole('alert')).toBeInTheDocument();
  fireEvent.click(reprendre);
  await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  expect(screen.getByRole('button', { name: /Préparer la synchronisation/ })).toBeEnabled();
});

it('ignore la reprise du dossier précédent', async () => {
  let finir!: (valeur: ReturnType<typeof etat>) => void;
  api.reprendreIndexSync.mockReturnValue(new Promise((resolve) => { finir = resolve; }));
  const vue = render(<ProjectSyncSection projectId="A" />);
  fireEvent.click(await screen.findByRole('button', { name: 'Réessayer la restitution' }));
  api.etatSync.mockResolvedValue({ ...etat(true), racine: '/B' });
  vue.rerender(<ProjectSyncSection projectId="B" />);
  await screen.findByText('/B');
  finir(etat(false));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Réessayer la restitution' })).toBeEnabled());
  expect(screen.getByText('/B')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toBeInTheDocument();
});
