import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({ checkHealth: vi.fn().mockResolvedValue({ version: '0.84.0', status: 'healthy' }) }));
import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

afterEach(() => {
  cleanup();
  useBackendStore.getState().reset();
  vi.unstubAllGlobals();
});

it('affiche la phase Bêta et ouvre le lien de téléchargement de la bêta', async () => {
  useBackendStore.setState({ version: '0.84.0' });
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Serveur de versions indisponible')));
  render(<AboutTab />);
  expect(screen.getByText('Bêta')).toBeInTheDocument();
  expect(screen.getByText(/La communauté bêta/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
  expect(await screen.findByRole('link', { name: 'Télécharger THÉRÈSE manuellement' }))
    .toHaveAttribute('href', 'https://synoptia.fr/therese/beta/');
});
