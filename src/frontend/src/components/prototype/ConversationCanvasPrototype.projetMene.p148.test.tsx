/**
 * P-148, lot 3 : depuis la fenêtre d'un projet, chaque famille s'ouvre en un
 * clic, et la fenêtre ne reste jamais ouverte par-dessus la destination.
 *
 * La fenêtre est rendue à deux endroits : la vue Projets (clic sur une carte)
 * et le conteneur global des panneaux (palette, commandes). Chaque geste est
 * vérifié sur les deux montages, avec la cible du focus nommée (constat 13 de
 * la revue) : la carte cliquée et le champ de la palette disparaissent avec
 * la navigation, le focus ne doit jamais tomber sur la page.
 *
 * - conversation : le champ du message (composeur) ;
 * - fiche d'un contact : le titre du panneau de contexte ;
 * - tâches du projet : le titre de la vue Tâches ;
 * - document : le titre de la vue Documents (l'atelier s'ouvre dessous).
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { Contact, EnsembleDuProjet, Project } from '../../services/api';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { _viderSaisiesEnCours } from '../../lib/saisieEnCours';
import { runAction } from '../../lib/actionRegistry';
import { useChatStore } from '../../stores/chatStore';
import { useDocumentStore } from '../../stores/documentStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { useStatusStore } from '../../stores/statusStore';
import { useTaskStore } from '../../stores/taskStore';

const apiMemoire = vi.hoisted(() => ({
  listProjects: vi.fn(), lireLEnsembleDuProjet: vi.fn(), listContacts: vi.fn(),
}));
vi.mock('../../services/api/memory', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/memory')>()),
  ...apiMemoire,
}));
const apiTaches = vi.hoisted(() => ({ listTasks: vi.fn() }));
vi.mock('../../services/api/tasks', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/tasks')>()),
  ...apiTaches,
}));
vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  // Un modèle disponible : sans lui, le champ du message reste désactivé.
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'ollama', model: 'x', available_models: ['x'], available: true }),
}));

import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const PROJET: Project = {
  id: 'p-cuisine', name: 'Cuisine Roux', description: null, contact_id: 'c-camille', status: 'active',
  budget: null, notes: null, tags: null, created_at: '2026-09-20T10:00:00Z', updated_at: '2026-09-20T10:00:00Z',
};
const CAMILLE: Contact = {
  id: 'c-camille', first_name: 'Camille', last_name: 'Roux', company: 'Roux SARL', email: null, phone: null,
  address: null, notes: null, tags: null, stage: 'contact', score: 50, source: null, last_interaction: null,
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};
const ENSEMBLE: EnsembleDuProjet = {
  conversations: { total: 1, elements: [{ id: 'conv-devis', titre: 'Devis cuisine', mise_a_jour: '2026-09-25T08:00:00+00:00' }] },
  documents: { total: 1, elements: [{ id: 'doc-plan', titre: 'Plan de formation', statut: 'en_cours', mise_a_jour: '2026-09-24T08:00:00+00:00' }] },
  taches: {
    total: 9, ouvertes: 4, en_retard: 1,
    elements: [{ id: 't-1', titre: 'Commander le plan de travail', statut: 'todo', echeance: null, en_retard: false }],
  },
  contacts: { total: 1, ranges: 0, elements: [{ id: 'c-camille', first_name: 'Camille', last_name: 'Roux', company: 'Roux SARL', associe: true }] },
  livrables: { total: 0 }, fichiers: { total: 0, deposes: 0, indexes_sur_place: 0 }, rendez_vous: { total: 0 }, dossier_synchronise: { rattache: false },
  sous_dossiers: { total: 0 }, planning: { total: 0 }, indisponibles: [],
};

type Montage = 'vue Projets' | 'conteneur global';

async function ouvrirLaFenetre(montage: Montage) {
  render(<ConversationCanvasPrototype />);
  if (montage === 'vue Projets') {
    await act(async () => { runAction('projects.open'); });
    fireEvent.click(await screen.findByText(PROJET.name, {}, { timeout: 4000 }));
  } else {
    await act(async () => { usePanelStore.setState({ showProjectModal: true, editingProject: PROJET }); });
  }
  const fenetre = await screen.findByRole('dialog', { name: `Projet ${PROJET.name}` }, { timeout: 4000 });
  await within(fenetre).findByText('Devis cuisine');
  return fenetre;
}

async function fenetreFermee() {
  await waitFor(() => expect(screen.queryByRole('dialog', { name: `Projet ${PROJET.name}` })).toBeNull());
}

/** Une fenêtre qu'on ferme reste dans le DOM le temps de sa sortie animée : on attend qu'elle ait pu partir. */
async function fenetreToujoursOuverte() {
  await act(async () => { await new Promise((r) => setTimeout(r, 400)); });
  expect(screen.getByRole('dialog', { name: `Projet ${PROJET.name}` })).toBeInTheDocument();
}

const vueAffichee = () => screen.getByTestId('conversation-canvas-prototype').getAttribute('data-embedded-view');

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  usePanelStore.setState({
    showSettings: false, requestedSettingsTab: null, showSaveCommand: false, showContactModal: false,
    showProjectModal: false, editingProject: null, showBoardPanel: false, showShortcuts: false,
    showPromptLibrary: false, showCommandPalette: false, showConversationSidebar: false,
  } as never);
  _clearEscapeHandlers();
  _viderSaisiesEnCours();
  useNavigationStore.setState(useNavigationStore.getInitialState());
  usePersonalisationStore.setState({ skipDashboard: false });
  useDocumentStore.setState({ ouvertureDemandee: null } as never);
  useTaskStore.setState({
    isTaskFormOpen: false, currentTaskId: null, tasks: [],
    // Constat 12 : des filtres persistés d'une visite précédente.
    filterStatus: 'done', filterPriority: 'high', filterProjectId: null,
  } as never);
  // Connecté : hors ligne, le champ du message est désactivé et ne prend pas le focus.
  useStatusStore.setState({ notifications: [], connectionState: 'connected' } as never);
  apiMemoire.listProjects.mockResolvedValue([PROJET]);
  apiMemoire.lireLEnsembleDuProjet.mockResolvedValue(ENSEMBLE);
  apiMemoire.listContacts.mockResolvedValue([CAMILLE]);
  apiTaches.listTasks.mockResolvedValue([]);
});
afterEach(() => { _clearEscapeHandlers(); _viderSaisiesEnCours(); });

describe.each<Montage>(['vue Projets', 'conteneur global'])('P-148 : mener depuis la fenêtre ouverte par la %s', (montage) => {
  it('une conversation s’ouvre, la fenêtre se ferme, le focus est dans le champ du message', async () => {
    const fenetre = await ouvrirLaFenetre(montage);
    await act(async () => {
      fireEvent.click(within(fenetre).getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' }));
    });
    await fenetreFermee();
    expect(useChatStore.getState().currentConversationId).toBe('conv-devis');
    const composeur = await screen.findByTestId('chat-message-input');
    await waitFor(() => expect(document.activeElement).toBe(composeur));
    // Le focus ne repart pas après les sorties animées.
    await act(async () => { await new Promise((r) => setTimeout(r, 400)); });
    expect(document.activeElement).toBe(composeur);
  });

  it('le contact associé ouvre sa fiche, le focus sur le titre du panneau', async () => {
    const fenetre = await ouvrirLaFenetre(montage);
    await act(async () => {
      fireEvent.click(within(fenetre).getByRole('button', { name: 'Ouvrir la fiche de Camille Roux' }));
    });
    await fenetreFermee();
    const titre = await screen.findByText('Retrouver un contact', { selector: '#prototype-context-canvas-title' });
    await waitFor(() => expect(document.activeElement).toBe(titre));
    // Aucune vue au-dessous : la fiche s'ouvre dans le panneau de contexte.
    expect(vueAffichee()).toBe('accueil');
    expect(await screen.findAllByRole('heading', { name: 'Camille Roux' })).not.toHaveLength(0);
    await act(async () => { await new Promise((r) => setTimeout(r, 400)); });
    expect(document.activeElement).toBe(titre);
  });

  it('« Voir les 9 tâches dans Tâches » filtre sur le projet, remet statut et priorité à zéro, focus sur le titre de la vue', async () => {
    const fenetre = await ouvrirLaFenetre(montage);
    await act(async () => {
      fireEvent.click(within(fenetre).getByRole('button', { name: 'Voir les 9 tâches dans Tâches' }));
    });
    await fenetreFermee();
    await waitFor(() => expect(vueAffichee()).toBe('tasks'));
    const { filterProjectId, filterStatus, filterPriority } = useTaskStore.getState();
    expect({ filterProjectId, filterStatus, filterPriority }).toEqual({ filterProjectId: PROJET.id, filterStatus: null, filterPriority: null });
    await waitFor(() => expect(apiTaches.listTasks).toHaveBeenLastCalledWith({ project_id: PROJET.id }));
    const titre = document.getElementById('prototype-unified-view-title');
    expect(titre).toHaveTextContent('Tâches');
    await waitFor(() => expect(document.activeElement).toBe(titre));
    await act(async () => { await new Promise((r) => setTimeout(r, 400)); });
    expect(document.activeElement).toBe(titre);
  });

  it('un document s’ouvre dans la vue Documents, le focus sur le titre de la vue', async () => {
    const fenetre = await ouvrirLaFenetre(montage);
    const ouverture = vi.spyOn(useDocumentStore.getState(), 'demanderLOuverture');
    await act(async () => {
      fireEvent.click(within(fenetre).getByRole('button', { name: 'Ouvrir le document Plan de formation' }));
    });
    await fenetreFermee();
    await waitFor(() => expect(vueAffichee()).toBe('documents'));
    expect(ouverture).toHaveBeenCalledWith('doc-plan');
    const titre = document.getElementById('prototype-unified-view-title');
    expect(titre).toHaveTextContent('Documents');
    await waitFor(() => expect(document.activeElement).toBe(titre));
    await act(async () => { await new Promise((r) => setTimeout(r, 400)); });
    expect(document.activeElement).toBe(titre);
    ouverture.mockRestore();
  });

  it('pendant une réponse en cours, la navigation est refusée et la fenêtre reste ouverte', async () => {
    const fenetre = await ouvrirLaFenetre(montage);
    act(() => { useChatStore.setState({ isStreaming: true }); });
    await act(async () => {
      fireEvent.click(within(fenetre).getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' }));
    });
    await fenetreToujoursOuverte();
    expect(useChatStore.getState().currentConversationId).toBeNull();
    expect(useStatusStore.getState().notifications.map((n) => n.title)).toContain('Réponse en cours');
  });
});

describe('P-148 : un formulaire modifié sous la fenêtre retient la navigation (constat 11)', () => {
  it('la fenêtre reste ouverte et le dit ; le formulaire Tâche garde sa saisie et pose sa question', async () => {
    useTaskStore.setState({ isTaskFormOpen: true, currentTaskId: null } as never);
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('tasks.open'); });
    const titreDeLaTache = (await screen.findByLabelText(/Titre/, {}, { timeout: 4000 })) as HTMLInputElement;
    fireEvent.change(titreDeLaTache, { target: { value: 'Rappeler le carreleur' } });

    await act(async () => { usePanelStore.setState({ showProjectModal: true, editingProject: PROJET }); });
    const fenetre = await screen.findByRole('dialog', { name: `Projet ${PROJET.name}` });
    await within(fenetre).findByText('Devis cuisine');
    await act(async () => {
      fireEvent.click(within(fenetre).getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' }));
    });

    await fenetreToujoursOuverte();
    const message = within(fenetre).getByText(
      'Un formulaire modifié, sous cette fenêtre, attend ta réponse : ferme la fenêtre pour y répondre, puis rouvre le projet.',
    );
    expect(message.closest('[role="alert"]')).not.toBeNull();
    expect(useChatStore.getState().currentConversationId).toBeNull();
    expect(vueAffichee()).toBe('tasks');
    expect(titreDeLaTache).toHaveValue('Rappeler le carreleur');
    expect(screen.getAllByText('Abandonner les modifications ?').length).toBeGreaterThan(0);
  });
});
