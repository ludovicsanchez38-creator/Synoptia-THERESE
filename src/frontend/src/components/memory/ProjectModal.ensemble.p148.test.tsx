/**
 * P-148 : ouvrir un projet montre d'abord ce qu'il rassemble.
 *
 * La fenêtre d'un projet s'intitulait « Modifier le projet » et empilait un
 * formulaire, le dossier synchronisé, les livrables et les fichiers. Ses
 * conversations, ses documents, ses tâches et ses contacts n'y figuraient
 * pas, alors que l'état vide de la vue Projets promet de les rassembler.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact, EnsembleDuProjet, Project } from '../../services/api';
import { buildReplacementMap, maskContact, maskProject } from '../../lib/demoMask';
import { useDemoStore } from '../../stores/demoStore';

const api = vi.hoisted(() => ({
  listContacts: vi.fn(), listProjectFiles: vi.fn(), etatSync: vi.fn(),
  updateProject: vi.fn(), createProject: vi.fn(), deleteProject: vi.fn(),
  deleteFile: vi.fn(), uploadProjectFile: vi.fn(),
  definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
  lireLEnsembleDuProjet: vi.fn(),
}));
vi.mock('../../services/api', () => api);
vi.mock('../../services/api/crm-extended', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listDeliverables: vi.fn().mockResolvedValue([]),
  createDeliverable: vi.fn(),
}));

import { ProjectModal } from './ProjectModal';

const PROJET: Project = {
  id: 'p-cuisine', name: 'Cuisine Roux', description: null, contact_id: 'c-camille', status: 'active',
  budget: null, notes: null, tags: null, created_at: '2026-09-20T10:00:00Z', updated_at: '2026-09-20T10:00:00Z',
};
const CAMILLE: Contact = {
  id: 'c-camille', first_name: 'Camille', last_name: 'Roux', company: 'Roux SARL', email: null, phone: null,
  address: null, notes: null, tags: null, stage: 'contact', score: 50, source: null, last_interaction: null,
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

function ensemble(partiel: Partial<EnsembleDuProjet> = {}): EnsembleDuProjet {
  return {
    conversations: { total: 1, elements: [{ id: 'conv-1', titre: 'Devis cuisine', mise_a_jour: '2026-09-25T08:00:00+00:00' }] },
    documents: { total: 1, elements: [{ id: 'doc-1', titre: 'Plan de formation', statut: 'termine', mise_a_jour: '2026-09-24T08:00:00+00:00' }] },
    taches: {
      total: 2, ouvertes: 1, en_retard: 1,
      elements: [
        { id: 't-1', titre: 'Commander le plan de travail', statut: 'todo', echeance: '2026-09-20T12:00:00', en_retard: true },
        { id: 't-2', titre: 'Métrer la pièce', statut: 'done', echeance: null, en_retard: false },
      ],
    },
    contacts: {
      total: 2, ranges: 1,
      elements: [
        { id: 'c-camille', first_name: 'Camille', last_name: 'Roux', company: 'Roux SARL', associe: true },
        { id: 'c-julien', first_name: 'Julien', last_name: 'Garnier', company: null, associe: false },
      ],
    },
    livrables: { total: 0 }, fichiers: { total: 0, deposes: 0, indexes_sur_place: 0 }, rendez_vous: { total: 0 }, dossier_synchronise: { rattache: false },
    sous_dossiers: { total: 0 }, planning: { total: 0, ressources: 0, calculs: 0 },
    indisponibles: [],
    ...partiel,
  };
}

const VIDE = ensemble({
  conversations: { total: 0, elements: [] },
  documents: { total: 0, elements: [] },
  taches: { total: 0, ouvertes: 0, en_retard: 0, elements: [] },
  contacts: { total: 0, ranges: 0, elements: [] },
});

async function ouvrir(projet: Project | null = PROJET) {
  await act(async () => {
    render(<ProjectModal isOpen onClose={vi.fn()} project={projet} />);
  });
}

function avant(a: Element, b: Element): boolean {
  return Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
}

describe('P-148 : la fenêtre du projet, une vue d’ensemble d’abord', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listContacts.mockResolvedValue([CAMILLE]);
    api.listProjectFiles.mockResolvedValue({ files: [], total: 0, truncated: false });
    api.etatSync.mockResolvedValue(null);
    api.lireLEnsembleDuProjet.mockResolvedValue(ensemble());
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });
  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('la fenêtre porte le nom du projet et le dit à qui ne la voit pas', async () => {
    await ouvrir();
    const fenetre = screen.getByRole('dialog', { name: 'Projet Cuisine Roux' });
    expect(within(fenetre).getByRole('heading', { level: 2, name: 'Cuisine Roux' })).toBeInTheDocument();
    expect(within(fenetre).getByText('Ce qu’il rassemble, puis ses informations')).toBeInTheDocument();
    expect(screen.queryByText('Modifier le projet')).toBeNull();
  });

  it('les quatre lignes précèdent Livrables, Fichiers et Dossier synchronisé, qui précèdent Informations du projet', async () => {
    await ouvrir();
    await screen.findByText('Devis cuisine');
    const lignes = ['Conversations (1)', 'Documents (1)', 'Tâches (2)', 'Contacts (2)']
      .map((nom) => screen.getByRole('heading', { level: 4, name: nom }));
    const livrables = screen.getByText('Livrables');
    const fichiers = screen.getByText('Fichiers du projet');
    const dossier = screen.getByRole('heading', { name: 'Dossier synchronisé' });
    const informations = screen.getByRole('heading', { level: 3, name: 'Informations du projet' });

    for (let i = 1; i < lignes.length; i += 1) expect(avant(lignes[i - 1], lignes[i])).toBe(true);
    expect(avant(lignes[3], livrables)).toBe(true);
    expect(avant(livrables, fichiers)).toBe(true);
    expect(avant(fichiers, dossier)).toBe(true);
    expect(avant(dossier, informations)).toBe(true);
    expect(avant(informations, screen.getByLabelText(/Nom du projet/))).toBe(true);
  });

  it('en édition, le focus initial est sur le titre du projet ; en création, sur « Nom »', async () => {
    await ouvrir();
    await waitFor(() => expect(screen.getByRole('heading', { level: 2, name: 'Cuisine Roux' })).toHaveFocus());
    cleanup();
    await ouvrir(null);
    await waitFor(() => expect(screen.getByLabelText(/Nom du projet/)).toHaveFocus());
    expect(screen.queryByRole('heading', { level: 3, name: 'Ce que rassemble ce projet' })).toBeNull();
  });

  it('chaque ligne est une liste nommée par son libellé et son total, le total dans le texte', async () => {
    await ouvrir();
    const conversations = await screen.findByRole('list', { name: 'Conversations (1)' });
    expect(within(conversations).getByText('Devis cuisine')).toBeInTheDocument();
    const taches = screen.getByRole('list', { name: 'Tâches (2)' });
    expect(within(taches).getByText('Commander le plan de travail')).toBeInTheDocument();
    expect(screen.getByText('1 ouverte, dont 1 en retard')).toBeInTheDocument();
    const contacts = screen.getByRole('list', { name: 'Contacts (2)' });
    expect(within(contacts).getByText('Camille Roux')).toBeInTheDocument();
    expect(within(contacts).getByText('Contact associé')).toBeInTheDocument();
    expect(api.lireLEnsembleDuProjet).toHaveBeenCalledWith(PROJET.id, 5);
  });

  it('chargement : chaque ligne le dit, sans alerte ni texte du vide', async () => {
    api.lireLEnsembleDuProjet.mockReturnValue(new Promise(() => {}));
    await ouvrir();
    expect(screen.getByRole('heading', { level: 4, name: 'Conversations' })).toBeInTheDocument();
    expect(screen.getAllByText('Chargement…').length).toBeGreaterThanOrEqual(4);
    expect(screen.queryByText(/Aucune conversation rattachée/)).toBeNull();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('panne : un bandeau avec « Réessayer », qui relit', async () => {
    api.lireLEnsembleDuProjet.mockRejectedValueOnce(new Error('réseau')).mockResolvedValueOnce(ensemble());
    await ouvrir();
    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent('Ce que rassemble ce projet n’a pas pu être lu.');
    expect(screen.queryByText(/Aucune conversation rattachée/)).toBeNull();
    await act(async () => { fireEvent.click(within(alerte).getByRole('button', { name: 'Réessayer' })); });
    expect(await screen.findByText('Devis cuisine')).toBeInTheDocument();
    expect(api.lireLEnsembleDuProjet).toHaveBeenCalledTimes(2);
  });

  it('une famille illisible est une panne sur sa ligne, jamais un zéro', async () => {
    api.lireLEnsembleDuProjet.mockResolvedValue(ensemble({ taches: null, indisponibles: ['taches'] }));
    await ouvrir();
    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent('Tâches : lecture impossible pour l’instant.');
    expect(screen.queryByText(/Aucune tâche/)).toBeNull();
    expect(screen.getByText('Devis cuisine')).toBeInTheDocument();
  });

  it('vide : chaque ligne dit comment rattacher', async () => {
    api.lireLEnsembleDuProjet.mockResolvedValue(VIDE);
    await ouvrir();
    expect(await screen.findByText('Aucune conversation rattachée. Une conversation se rattache depuis son sélecteur de projet.')).toBeInTheDocument();
    expect(screen.getByText('Aucun document. Un document se rattache à un projet à sa création.')).toBeInTheDocument();
    expect(screen.getByText('Aucune tâche. Une tâche se rattache à un projet depuis son formulaire.')).toBeInTheDocument();
    expect(screen.getByText('Aucun contact associé : choisis-le plus bas, dans Informations du projet.')).toBeInTheDocument();
  });

  it('« Tout afficher » relit avec limite=200 et dit « liste incomplète » au-delà', async () => {
    const cinq = Array.from({ length: 5 }, (_, i) => ({ id: `c${i}`, titre: `Échange ${i}`, mise_a_jour: '2026-09-25T08:00:00+00:00' }));
    const deuxCents = Array.from({ length: 200 }, (_, i) => ({ id: `c${i}`, titre: `Échange ${i}`, mise_a_jour: '2026-09-25T08:00:00+00:00' }));
    api.lireLEnsembleDuProjet
      .mockResolvedValueOnce(ensemble({ conversations: { total: 240, elements: cinq } }))
      .mockResolvedValueOnce(ensemble({ conversations: { total: 240, elements: deuxCents } }));
    await ouvrir();
    await act(async () => { fireEvent.click(await screen.findByRole('button', { name: 'Tout afficher (240)' })); });

    expect(api.lireLEnsembleDuProjet).toHaveBeenLastCalledWith(PROJET.id, 200);
    expect(within(screen.getByRole('list', { name: 'Conversations (240)' })).getAllByRole('listitem')).toHaveLength(200);
    expect(screen.getByText('Liste incomplète : les 200 plus récentes sont affichées.')).toBeInTheDocument();
    // Le bouton parti, le focus revient sur la ligne au lieu de tomber sur la page.
    await waitFor(() => expect(screen.getByRole('heading', { level: 4, name: 'Conversations (240)' })).toHaveFocus());
  });

  it('démonstration : le titre passe par maskProject et aucun texte n’apparaît avant les contacts', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    api.listContacts.mockReturnValue(new Promise(() => {}));
    await ouvrir();
    const pseudonyme = maskProject({ id: PROJET.id, name: PROJET.name }).name;

    expect(screen.getByRole('dialog', { name: `Projet ${pseudonyme}` })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: pseudonyme })).toBeInTheDocument();
    expect(screen.queryByText('Consulter le projet')).toBeNull();
    await waitFor(() => expect(api.lireLEnsembleDuProjet).toHaveBeenCalled());
    for (const secret of ['Cuisine Roux', 'Devis cuisine', 'Plan de formation', 'Camille Roux', 'Julien Garnier', 'Commander le plan de travail']) {
      expect(screen.queryByText(secret)).toBeNull();
    }
    // Le champ « Nom » et le titre donnent le même pseudonyme.
    expect(screen.getByLabelText(/Nom du projet/)).toHaveValue(pseudonyme);
  });

  // Revue P-148, constat 11 : « le contenu défilant contient ses éléments
  // positionnés » (l'étiquette sr-only de « Nouveau livrable » faisait
  // défiler la fenêtre entière et cachait son en-tête) se mesure dans la
  // recette navigateur scripts-recette/recette-p148.mjs : l'en-tête ne bouge
  // pas quand la confirmation est ramenée dans la vue. jsdom ne calcule ni
  // mise en page ni défilement ; une classe n'y prouvait rien.

  it('démonstration, contacts lus : les noms de la vue d’ensemble sont masqués comme ailleurs', async () => {
    const remplacements = buildReplacementMap([CAMILLE], [PROJET]);
    useDemoStore.setState({ enabled: true, replacementMap: new Map(remplacements) });
    await ouvrir();
    const contacts = await screen.findByRole('list', { name: 'Contacts (2)' });
    expect(within(contacts).queryByText('Camille Roux')).toBeNull();
    // Le même pseudonyme que le sélecteur « Contact associé » de la fenêtre.
    const camille = maskContact(CAMILLE);
    expect(within(contacts).getByText(`${camille.first_name} ${camille.last_name}`)).toBeInTheDocument();
  });

  it.each([
    ['carnet lu, sans Julien', () => api.listContacts.mockResolvedValue([CAMILLE])],
    ['carnet jamais lu', () => api.listContacts.mockReturnValue(new Promise(() => {}))],
  ])('revue P-148, constat 2 : en démonstration, un contact rangé absent du carnet ne paraît jamais (%s)', async (_cas, carnet) => {
    carnet();
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    await ouvrir();
    const contacts = await screen.findByRole('list', { name: 'Contacts (2)' });
    for (const reel of ['Julien Garnier', 'Julien', 'Garnier', 'Camille Roux', 'Roux SARL']) {
      expect(screen.queryByText(reel)).toBeNull();
      expect(contacts).not.toHaveTextContent(reel);
    }
    const julien = maskContact({ id: 'c-julien', first_name: 'Julien', last_name: 'Garnier', company: null });
    expect(within(contacts).getByText(`${julien.first_name} ${julien.last_name}`)).toBeInTheDocument();
    expect(within(contacts).getByRole('button', { name: `Ouvrir la fiche de ${julien.first_name} ${julien.last_name}` })).toBeInTheDocument();
  });
});
