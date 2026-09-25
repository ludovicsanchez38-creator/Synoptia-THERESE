/**
 * P-144 (persona Nathalie, cycle 13) : « Ouvrir la fiche » du Pipeline ouvrait
 * l'onglet Activités : nom, entreprise, prestations, historique, mais ni
 * e-mail, ni téléphone, ni étape, ni score. La fiche montre désormais ses
 * coordonnées, son étape (le nom d'écran, pas le code) et son score, avec
 * l'explication du score.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';

const elodie = vi.hoisted(() => ({
  id: 'ct-1', first_name: 'Élodie', last_name: 'Martin', company: 'Boulangerie Martin',
  email: 'elodie@boulangerie-exemple.fr', phone: '06 12 34 56 78', address: null, notes: null, tags: null,
  scope: 'global', stage: 'discovery', score: 105, source: null, last_interaction: null,
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
}));

const contactsLus = vi.hoisted(() => vi.fn());
const etapeChangee = vi.hoisted(() => vi.fn());

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listProjects: vi.fn().mockResolvedValue([]), listActivities: vi.fn().mockResolvedValue([]), updateContactStage: (...a: unknown[]) => etapeChangee(...a) };
});
vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...reel, listContacts: (...a: unknown[]) => contactsLus(...a) };
});
vi.mock('../../services/api/prestations', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/prestations')>('../../services/api/prestations');
  return { ...reel, listerLesPrestations: vi.fn().mockResolvedValue([]) };
});

import { CRMPanel } from './CRMPanel';

describe('P-132 : l’étape se change depuis la fiche', () => {
  beforeEach(() => {
    contactsLus.mockResolvedValue([elodie]);
    etapeChangee.mockResolvedValue({ ...elodie, stage: 'proposition', score: 120 });
    useCRMStore.setState({ projects: [], activeTab: 'activities' });
    useContactsStore.setState({ contacts: [elodie] as never, loaded: true, loading: false, error: null, selectedContactId: 'ct-1', truncated: false });
  });

  it('choisir une étape passe par le même chemin que le glisser (activité et score)', async () => {
    render(<CRMPanel standalone />);
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    const etape = within(fiche).getByLabelText('Étape') as HTMLSelectElement;
    expect(etape.value).toBe('discovery');
    fireEvent.change(etape, { target: { value: 'proposition' } });
    await waitFor(() => expect(etapeChangee).toHaveBeenCalledWith('ct-1', 'proposition'));
    await waitFor(() => expect((within(fiche).getByLabelText('Étape') as HTMLSelectElement).value).toBe('proposition'));
  });
});

describe('P-144 : « Ouvrir la fiche » ouvre une vraie fiche', () => {
  beforeEach(() => {
    contactsLus.mockResolvedValue([elodie]);
    useCRMStore.setState({ projects: [], activeTab: 'activities' });
    useContactsStore.setState({ contacts: [elodie] as never, loaded: true, loading: false, error: null, selectedContactId: 'ct-1', truncated: false });
  });

  it('montre e-mail, téléphone, étape et score', async () => {
    render(<CRMPanel standalone />);
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });

    expect(within(fiche).getByText('elodie@boulangerie-exemple.fr')).toBeInTheDocument();
    expect(within(fiche).getByText('06 12 34 56 78')).toBeInTheDocument();
    expect((within(fiche).getByLabelText('Étape') as HTMLSelectElement).value).toBe('discovery');
    expect(within(fiche).getByText('105')).toBeInTheDocument();
    // P-152 : l'explication se déplie depuis un bouton, lisible au clavier.
    fireEvent.click(within(fiche).getByRole('button', { name: 'Expliquer le score' }));
    expect(within(fiche).getByText(/Score de potentiel commercial/)).toBeInTheDocument();
  });

  it('une coordonnée absente se dit, sans case vide', async () => {
    contactsLus.mockResolvedValue([{ ...elodie, phone: null }]);
    useContactsStore.setState({ contacts: [{ ...elodie, phone: null }] as never });
    render(<CRMPanel standalone />);
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });

    expect(within(fiche).getByText('Non renseigné')).toBeInTheDocument();
  });
});
