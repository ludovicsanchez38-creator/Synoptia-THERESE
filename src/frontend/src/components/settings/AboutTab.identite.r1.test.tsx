import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({
  checkHealth: vi.fn().mockResolvedValue({ version: '0.83.0', status: 'healthy' }),
}));
import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

describe('R1-1 : identité incomplète de la livraison installée', () => {
  beforeEach(() => {
    useBackendStore.getState().reset();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ tag_name: 'v0.83.0-alpha.2', assets: [] }],
    }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it('ne conclut pas à jour avec le numéro sans suffixe renvoyé par le moteur', async () => {
    render(<AboutTab />);
    await screen.findByText('0.83.0');
    fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/version exacte de la livraison installée/);
    expect(screen.queryByText(/THÉRÈSE est à jour|Nouvelle version disponible/)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE manuellement' }))
      .toHaveAttribute('href', 'https://synoptia.fr/therese/alpha/');
  });
});
