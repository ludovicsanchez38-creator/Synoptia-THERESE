/**
 * B-1840 : l'étape Profil renaît vide à chaque montage. L'assistant ne la
 * garde montée qu'à l'étape courante, donc un retour arrière perd la fiche
 * que Continuer vient d'enregistrer, et le clic suivant envoie des chaînes
 * vides à la place.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
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

  it.each(['Nom saisi', ''])('le profil relu conserve la saisie %j et complète les champs intacts', async (nomSaisi) => {
    let finirLecture!: (resultat: typeof fiche) => void;
    apiMocks.getProfile.mockReturnValue(new Promise<typeof fiche>((resoudre) => { finirLecture = resoudre; }));
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText(/Nom complet/);
    fireEvent.change(champ, { target: { value: 'Texte temporaire' } });
    fireEvent.change(champ, { target: { value: nomSaisi } });

    await act(async () => { finirLecture(fiche); });
    expect(champ).toHaveValue(nomSaisi);
    expect(screen.getByDisplayValue(fiche.company)).toBeInTheDocument();
    expect(screen.getByDisplayValue(fiche.email)).toBeInTheDocument();
    expect(screen.getByDisplayValue(fiche.siret)).toBeInTheDocument();
  });

  it.each([
    ['name', /^Nom complet/, 'Nouveau nom', false],
    ['nickname', /^Surnom/, '', false],
    ['company', /^Entreprise/, 'Atelier Test', false],
    ['role', /^Rôle/, 'Responsable', false],
    ['email', /^Email/, 'camille@example.test', false],
    ['location', /^Localisation/, 'Toulouse', false],
    ['context', /^Contexte additionnel/, '', false],
    ['address', /^Adresse \(facturation\)/, '1 rue du Test', true],
    ['siret', /^SIRET/, '11111111100011', true],
    ['tva_intra', /^TVA intracommunautaire/, '', true],
  ] as const)('rejoue la fusion et l’enregistrement du champ %s', async (cle, etiquette, valeur, voletFacturation) => {
    let finirLecture!: (resultat: typeof fiche) => void;
    apiMocks.getProfile.mockReturnValue(new Promise<typeof fiche>((resoudre) => { finirLecture = resoudre; }));
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    if (voletFacturation) fireEvent.click(screen.getByRole('button', { name: /Je facture avec THÉRÈSE/ }));
    const champ = screen.getByLabelText(etiquette);
    fireEvent.change(champ, { target: { value: 'Saisie temporaire' } });
    fireEvent.change(champ, { target: { value: valeur } });

    const continuer = screen.getByTestId('onboarding-next-btn');
    expect(continuer).toBeDisabled();
    fireEvent.click(continuer);
    expect(apiMocks.setProfile).not.toHaveBeenCalled();
    await act(async () => { finirLecture(fiche); });
    expect(champ).toHaveValue(valeur);
    fireEvent.click(continuer);
    await waitFor(() => expect(apiMocks.setProfile).toHaveBeenCalledExactlyOnceWith({ ...fiche, [cle]: valeur }));
  });
});
