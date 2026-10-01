/**
 * B-1752 : ouvrir une fiche retire le bouton du Pipeline qui portait le focus.
 * Le panneau réel doit transmettre ce focus à la destination, une seule fois.
 * Le délai contrôlé ci-dessous représente la sortie AnimatePresence(mode=wait),
 * sans doubler le CRM, ses stores, sa fiche ni ses commandes.
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { Contact } from '../../services/api/memory';
import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';

const lectures = vi.hoisted(() => ({
  contacts: vi.fn(),
  projets: vi.fn(),
  activites: vi.fn(),
  prestations: vi.fn(),
}));
const sortie = vi.hoisted(() => ({
  retenirFiche: false,
  libererFiche: null as (() => void) | null,
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listProjects: lectures.projets, listActivities: lectures.activites };
});
vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...reel, listContacts: lectures.contacts };
});
vi.mock('../../services/api/prestations', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/prestations')>('../../services/api/prestations');
  return { ...reel, listerLesPrestations: lectures.prestations };
});
vi.mock('framer-motion', async () => {
  const reel = await vi.importActual<typeof import('framer-motion')>('framer-motion');
  const React = await import('react');
  return {
    ...reel,
    AnimatePresence: function PresenceControlee({ children, mode }: { children: React.ReactNode; mode?: string }) {
      const [liberee, liberer] = React.useState(false);
      const ficheArrive = React.Children.toArray(children).some((enfant) =>
        React.isValidElement(enfant) && String(enfant.key).endsWith('activities'),
      );
      if (mode === 'wait' && sortie.retenirFiche && ficheArrive && !liberee) {
        sortie.libererFiche = () => liberer(true);
        return null;
      }
      return <>{children}</>;
    },
  };
});

import { CRMPanel } from './CRMPanel';

const temoin: Contact = {
  id: 'c15-focus-fiche', first_name: 'Élodie', last_name: 'Martin', company: 'Entreprise témoin',
  email: 'elodie@example.test', phone: null, address: null, notes: null, tags: null,
  scope: 'global', stage: 'discovery', score: 60, source: null, last_interaction: null,
  created_at: '2026-09-30T00:00:00Z', updated_at: '2026-09-30T00:00:00Z',
};

/** jsdom ne produit pas le clic implicite d'Entrée. La recette Chromium de
 * B-1752 couvre cet événement natif ; ici le clic traverse le vrai CRMPanel. */
function activerEntree(bouton: HTMLElement) {
  bouton.focus();
  fireEvent.keyDown(bouton, { key: 'Enter', code: 'Enter' });
  fireEvent.keyUp(bouton, { key: 'Enter', code: 'Enter' });
  fireEvent.click(bouton);
}

async function rendrePipeline() {
  render(<CRMPanel standalone />);
  const ouvrir = await screen.findByRole('button', { name: 'Ouvrir la fiche' });
  await waitFor(() => expect(lectures.contacts).toHaveBeenCalled());
  return ouvrir;
}

beforeEach(() => {
  vi.clearAllMocks();
  sortie.retenirFiche = false;
  sortie.libererFiche = null;
  lectures.contacts.mockResolvedValue([temoin]);
  lectures.projets.mockResolvedValue([]);
  lectures.activites.mockResolvedValue([]);
  lectures.prestations.mockResolvedValue([]);
  useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
  useContactsStore.setState({
    contacts: [temoin], selectedContactId: null, searchResults: null,
    loading: false, loaded: true, error: null, truncated: false,
  });
});
afterEach(() => cleanup());

describe('B-1752 : le focus suit l’ouverture de la fiche CRM', () => {
  it('Entrée depuis le Pipeline amène le focus dans la fiche visible', async () => {
    const ouvrir = await rendrePipeline();
    activerEntree(ouvrir);
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    const panneau = screen.getByRole('tabpanel', { name: 'Activités' });

    await waitFor(() => expect(fiche).toBeVisible());
    expect(ouvrir.isConnected).toBe(false);
    await waitFor(() => expect(panneau.contains(document.activeElement)).toBe(true));
    expect(document.activeElement).not.toBe(document.body);
    expect(useContactsStore.getState().selectedContactId).toBe(temoin.id);
    expect(lectures.activites).toHaveBeenCalledWith(expect.objectContaining({ contact_id: temoin.id }));
  });

  it('transmet le focus perdu quand la fiche arrive après la sortie du Pipeline', async () => {
    sortie.retenirFiche = true;
    const ouvrir = await rendrePipeline();
    activerEntree(ouvrir);
    expect(ouvrir.isConnected).toBe(false);
    expect(document.activeElement).toBe(document.body);
    expect(screen.queryByRole('region', { name: 'Fiche de Élodie Martin' })).toBeNull();

    await act(async () => sortie.libererFiche!());
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    await waitFor(() => expect(fiche).toBeVisible());
    expect(document.activeElement).toBe(fiche);
  });

  it('conserve le focus posé ailleurs pendant la sortie du Pipeline', async () => {
    sortie.retenirFiche = true;
    const ouvrir = await rendrePipeline();
    activerEntree(ouvrir);
    expect(screen.queryByRole('region', { name: 'Fiche de Élodie Martin' })).toBeNull();
    expect(ouvrir.isConnected).toBe(false);
    expect(sortie.libererFiche).not.toBeNull();
    const importer = screen.getByRole('button', { name: 'Importer (.vcf)' });
    importer.focus();

    await act(async () => sortie.libererFiche!());
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    await waitFor(() => expect(fiche).toBeVisible());
    expect(document.activeElement).toBe(importer);
  });

  it('une relecture de la fiche ou un retour par les onglets ne reprend pas le focus', async () => {
    activerEntree(await rendrePipeline());
    await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    const importer = screen.getByRole('button', { name: 'Importer (.vcf)' });
    importer.focus();

    act(() => useContactsStore.getState().upsertLocal({ ...temoin, score: 75 }));
    await screen.findByText('75');
    expect(document.activeElement).toBe(importer);

    const pipeline = screen.getByRole('tab', { name: 'Pipeline' });
    pipeline.focus();
    fireEvent.click(pipeline);
    await screen.findByRole('button', { name: 'Ouvrir la fiche' });
    const activites = screen.getByRole('tab', { name: 'Activités' });
    activites.focus();
    fireEvent.click(activites);

    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    await waitFor(() => expect(fiche).toBeVisible());
    expect(document.activeElement).toBe(activites);
  });
});
