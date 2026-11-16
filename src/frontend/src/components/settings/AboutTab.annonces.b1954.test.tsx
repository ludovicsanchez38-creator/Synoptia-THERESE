import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../services/api', () => ({ checkHealth: vi.fn() }));
import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

function reponse(tag: string) {
  return { ok: true, json: async () => [{ tag_name: tag, name: tag, assets: [] }] } as Response;
}
function verifier() {
  fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
}

describe('B-1954 : tous les états de vérification sont annoncés', () => {
  beforeEach(() => {
    useBackendStore.setState({ version: '0.83.0', status: 'connected', error: null });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('annonce la vérification en cours puis la nouvelle version dans la même région', async () => {
    let terminer!: (v: Response) => void;
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>((resolve) => { terminer = resolve; })));
    render(<AboutTab />);
    verifier();
    let statut: HTMLElement | undefined;
    try {
      statut = screen.getByRole('status');
      expect(statut).toHaveTextContent(/Vérification.*en cours/);
    } finally {
      await act(async () => terminer(reponse('v0.84.0')));
    }
    await waitFor(() => expect(statut).toHaveTextContent('Nouvelle version disponible : v0.84.0'));
    expect(screen.getByRole('status')).toBe(statut);
  });

  it('annonce une mise à jour disponible', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reponse('v0.84.0')));
    render(<AboutTab />);
    verifier();
    await screen.findByText('Nouvelle version disponible : v0.84.0');
    expect(screen.getByRole('status')).toHaveTextContent('Nouvelle version disponible : v0.84.0');
  });

  it('continue d’annoncer que la version est à jour', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reponse('v0.83.0')));
    render(<AboutTab />);
    verifier();
    await screen.findByText('THÉRÈSE est à jour (v0.83.0)');
    expect(screen.getByRole('status')).toHaveTextContent('THÉRÈSE est à jour (v0.83.0)');
  });
});
