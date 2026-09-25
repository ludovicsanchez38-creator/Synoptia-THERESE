/**
 * P-112 (persona Claire, cycle 13) : l'assistant s'arrêtait à l'identité ; la
 * facturation se complétait ensuite par une carte de l'Accueil puis un
 * défilement dans Paramètres. Un volet facultatif « Je facture avec
 * THÉRÈSE » permet de tout régler d'un coup.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfileStep } from './ProfileStep';

const apiMocks = vi.hoisted(() => ({
  setProfile: vi.fn(),
  importClaudeMd: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

describe('P-112 : la facturation dès la mise en route', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.setProfile.mockResolvedValue({});
  });

  it('le volet est replié par défaut, sans champ de facturation', () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const bascule = screen.getByRole('button', { name: /Je facture avec THÉRÈSE/ });
    expect(bascule).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByLabelText(/SIRET/)).toBeNull();
  });

  it('déplié et rempli, l’adresse, le SIRET et la TVA partent avec le profil', async () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Nom complet *'), { target: { value: 'Claire Exemple' } });
    fireEvent.click(screen.getByRole('button', { name: /Je facture avec THÉRÈSE/ }));
    fireEvent.change(screen.getByLabelText(/Adresse/), { target: { value: '1 rue de la Paix, 04100 Manosque' } });
    fireEvent.change(screen.getByLabelText(/SIRET/), { target: { value: '999 888 779 00009' } });
    fireEvent.change(screen.getByLabelText(/TVA intracommunautaire/), { target: { value: 'FR00999888779' } });
    await act(async () => {
      fireEvent.click(screen.getByTestId('onboarding-next-btn'));
      await Promise.resolve();
    });
    expect(apiMocks.setProfile).toHaveBeenCalledWith(expect.objectContaining({
      name: 'Claire Exemple',
      address: '1 rue de la Paix, 04100 Manosque',
      siret: '999 888 779 00009',
      tva_intra: 'FR00999888779',
    }));
  });
});
