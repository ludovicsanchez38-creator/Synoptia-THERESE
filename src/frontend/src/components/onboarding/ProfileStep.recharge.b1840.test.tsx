/**
 * B-1840 : l'étape Profil renaît vide à chaque montage. L'assistant ne la
 * garde montée qu'à l'étape courante, donc un retour arrière perd la fiche
 * que Continuer vient d'enregistrer, et le clic suivant envoie des chaînes
 * vides à la place.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfileStep } from './ProfileStep';

const fiche = {
  name: 'Camille Martin',
  nickname: 'Cam',
  company: 'Atelier Martin',
  role: 'Gérante',
  email: 'camille@atelier-martin.fr',
  location: 'Manosque',
  context: 'Plomberie, quatre personnes',
  address: '12 rue des Oliviers, 04100 Manosque',
  siret: '12345678900010',
  tva_intra: 'FR00123456789',
};

const apiMocks = vi.hoisted(() => ({
  getProfile: vi.fn(),
  setProfile: vi.fn(),
  importClaudeMd: vi.fn(),
  getConfigStats: vi.fn().mockResolvedValue({ data_dir: '/tmp/therese-b1840' }),
}));

vi.mock('../../services/api', () => apiMocks);

describe('ProfileStep recharge la fiche au montage (B-1840)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getProfile.mockResolvedValue(fiche);
    apiMocks.setProfile.mockResolvedValue(fiche);
  });

  it('Continuer renvoie l’entreprise, l’e-mail, le contexte et le SIRET déjà enregistrés', async () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(await screen.findByDisplayValue('Atelier Martin')).toBeInTheDocument();
    expect(screen.getByDisplayValue('camille@atelier-martin.fr')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Plomberie, quatre personnes')).toBeInTheDocument();
    expect(screen.getByDisplayValue('12345678900010')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('onboarding-next-btn'));

    await waitFor(() => expect(apiMocks.setProfile).toHaveBeenCalledTimes(1));
    expect(apiMocks.setProfile).toHaveBeenCalledWith(expect.objectContaining({
      name: 'Camille Martin',
      company: 'Atelier Martin',
      email: 'camille@atelier-martin.fr',
      context: 'Plomberie, quatre personnes',
      siret: '12345678900010',
      address: '12 rue des Oliviers, 04100 Manosque',
    }));
  });
});
