import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({ checkHealth: vi.fn() }));
import { checkHealth } from '../../services/api';
import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

const moteur = { version: '0.83.0-alpha.1', status: 'healthy' };
function verifier() {
  fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
}

describe('R1-5 : réessayer la lecture de la version', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(checkHealth).mockReset();
    useBackendStore.getState().reset();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, json: async () => [{ tag_name: 'v0.83.0-alpha.2', assets: [] }],
    }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it('relit le moteur revenu puis compare la version récupérée dans le même clic', async () => {
    vi.mocked(checkHealth).mockRejectedValueOnce(new Error('Moteur indisponible')).mockResolvedValue(moteur);
    render(<AboutTab />);
    await screen.findByRole('alert');
    verifier();
    await waitFor(() => expect(checkHealth).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('Nouvelle version disponible : v0.83.0-alpha.2')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(useBackendStore.getState().version).toBe(moteur.version);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('partage la lecture encore en cours au montage et désactive les doubles clics', async () => {
    let terminer!: (valeur: typeof moteur) => void;
    vi.mocked(checkHealth).mockReturnValue(new Promise((resolve) => { terminer = resolve; }));
    render(<AboutTab />);
    verifier();
    try {
      expect(screen.getByRole('button', { name: 'Vérification...' })).toBeDisabled();
      expect(screen.getByRole('alert')).toHaveTextContent(/version installée/);
      expect(checkHealth).toHaveBeenCalledTimes(1);
      expect(fetch).not.toHaveBeenCalled();
    } finally {
      await act(async () => terminer(moteur));
    }
    await screen.findByText('Nouvelle version disponible : v0.83.0-alpha.2');
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('un deuxième échec garde le lien manuel et permet une troisième lecture', async () => {
    vi.mocked(checkHealth).mockRejectedValueOnce(new Error('Moteur indisponible'))
      .mockRejectedValueOnce(new Error('Toujours indisponible')).mockResolvedValue(moteur);
    render(<AboutTab />);
    await screen.findByRole('alert');
    verifier();
    await waitFor(() => expect(checkHealth).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Vérifier les mises à jour' })).toBeEnabled());
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE manuellement' })).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
    verifier();
    await screen.findByText('Nouvelle version disponible : v0.83.0-alpha.2');
    expect(checkHealth).toHaveBeenCalledTimes(3);
  });
});
