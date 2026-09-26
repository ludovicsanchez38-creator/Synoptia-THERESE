/**
 * P-148, lot 3 : le déroulé d'un clic dans la vue d'ensemble d'un projet.
 *
 * 1. Saisie modifiée (B-1392) : la destination est retenue et la question
 *    « Abandonner les modifications ? » passe avant ; « Continuer la saisie »
 *    annule la navigation.
 * 2. La demande part en événement annulable ; la coque l'annule quand elle
 *    refuse, et dit pourquoi.
 * 3. La fenêtre ne se ferme que si l'ouverture a été acceptée. Refusée par un
 *    formulaire modifié ailleurs (constat 11), elle le dit elle-même.
 */
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { EnsembleDuProjet, Project } from '../../services/api';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import {
  EVENEMENT_OUVRIR_TRAVAIL,
  refuserLOuverture,
  type DestinationDuTravail,
  type RefusDOuverture,
} from '../../lib/destinationDuTravail';

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
const ENSEMBLE: EnsembleDuProjet = {
  conversations: { total: 1, elements: [{ id: 'conv-devis', titre: 'Devis cuisine', mise_a_jour: '2026-09-25T08:00:00+00:00' }] },
  documents: { total: 1, elements: [{ id: 'doc-plan', titre: 'Plan de formation', statut: 'en_cours', mise_a_jour: '2026-09-24T08:00:00+00:00' }] },
  taches: { total: 1, ouvertes: 1, en_retard: 0, elements: [{ id: 't-1', titre: 'Métrer', statut: 'todo', echeance: null, en_retard: false }] },
  contacts: { total: 1, ranges: 0, elements: [{ id: 'c-camille', first_name: 'Camille', last_name: 'Roux', company: null, associe: true }] },
  livrables: { total: 0 }, fichiers: { total: 0, deposes: 0, indexes_sur_place: 0 }, rendez_vous: { total: 0 }, dossier_synchronise: { rattache: false },
  sous_dossiers: { total: 0 }, planning: { total: 0 }, indisponibles: [],
};
const QUESTION = 'Abandonner les modifications ?';

let demandes: DestinationDuTravail[] = [];
let refus: RefusDOuverture | null = null;
function coque(evenement: Event) {
  demandes.push((evenement as CustomEvent<DestinationDuTravail>).detail);
  if (refus) refuserLOuverture(evenement, refus);
}

async function ouvrir(onClose = vi.fn()) {
  await act(async () => { render(<ProjectModal isOpen onClose={onClose} project={PROJET} />); });
  await screen.findByText('Devis cuisine');
  return onClose;
}

describe('P-148 : mener depuis la fenêtre d’un projet', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listContacts.mockResolvedValue([]);
    api.listProjectFiles.mockResolvedValue({ files: [], total: 0, truncated: false });
    api.etatSync.mockResolvedValue(null);
    api.lireLEnsembleDuProjet.mockResolvedValue(ENSEMBLE);
    demandes = [];
    refus = null;
    window.addEventListener(EVENEMENT_OUVRIR_TRAVAIL, coque);
  });
  afterEach(() => {
    window.removeEventListener(EVENEMENT_OUVRIR_TRAVAIL, coque);
    cleanup();
    _clearEscapeHandlers();
  });

  it('chaque famille demande sa destination, et la fenêtre se ferme une fois acceptée', async () => {
    for (const [bouton, attendu] of [
      ['Ouvrir la conversation Devis cuisine', { kind: 'conversation', id: 'conv-devis' }],
      ['Ouvrir le document Plan de formation', { kind: 'document', id: 'doc-plan' }],
      ['Ouvrir la fiche de Camille Roux', { kind: 'contact', id: 'c-camille' }],
      ['Voir la tâche dans Tâches', { kind: 'taches-du-projet', projetId: PROJET.id }],
    ] as const) {
      demandes = [];
      const onClose = await ouvrir();
      await act(async () => { fireEvent.click(screen.getByRole('button', { name: bouton })); });
      expect(demandes).toEqual([attendu]);
      expect(onClose).toHaveBeenCalledTimes(1);
      cleanup();
    }
  });

  it('la demande est annulable : la coque peut la refuser', async () => {
    let annulable: boolean | null = null;
    const espion = (evenement: Event) => { annulable = evenement.cancelable; };
    window.addEventListener(EVENEMENT_OUVRIR_TRAVAIL, espion);
    await ouvrir();
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' })); });
    window.removeEventListener(EVENEMENT_OUVRIR_TRAVAIL, espion);
    expect(annulable).toBe(true);
  });

  it('saisie modifiée : la question passe avant, « Continuer la saisie » annule la navigation', async () => {
    const onClose = await ouvrir();
    fireEvent.change(screen.getByLabelText(/Nom du projet/), { target: { value: 'Cuisine Roux et fils' } });

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' })); });
    expect(screen.getByText(QUESTION)).toBeInTheDocument();
    expect(demandes).toEqual([]);

    fireEvent.click(screen.getByRole('button', { name: 'Continuer la saisie' }));
    expect(screen.queryByText(QUESTION)).toBeNull();
    expect(demandes).toEqual([]);
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/Nom du projet/)).toHaveValue('Cuisine Roux et fils');
  });

  it('saisie modifiée : « Abandonner » poursuit la navigation et ferme', async () => {
    const onClose = await ouvrir();
    fireEvent.change(screen.getByLabelText(/Nom du projet/), { target: { value: 'Cuisine Roux et fils' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la fiche de Camille Roux' })); });

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Abandonner' })); });
    expect(demandes).toEqual([{ kind: 'contact', id: 'c-camille' }]);
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(api.updateProject).not.toHaveBeenCalled();
  });

  it('saisie modifiée : Échap sur la question annule aussi la navigation retenue', async () => {
    const onClose = await ouvrir();
    fireEvent.change(screen.getByLabelText(/Nom du projet/), { target: { value: 'Cuisine Roux et fils' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' })); });
    act(() => { runTopEscapeHandler(); });
    expect(screen.queryByText(QUESTION)).toBeNull();

    // Un second Échap pose la question de fermeture : « Abandonner » ferme, sans naviguer.
    act(() => { runTopEscapeHandler(); });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Abandonner' })); });
    expect(demandes).toEqual([]);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('saisie modifiée : la croix, pendant la question, la change en question de fermeture', async () => {
    const onClose = await ouvrir();
    fireEvent.change(screen.getByLabelText(/Nom du projet/), { target: { value: 'Cuisine Roux et fils' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' })); });
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Abandonner' })); });
    expect(demandes).toEqual([]);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('refusée par un formulaire modifié ailleurs, la fenêtre reste ouverte et le dit', async () => {
    refus = 'saisie-en-cours';
    const onClose = await ouvrir();
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' })); });
    expect(onClose).not.toHaveBeenCalled();
    expect(within(screen.getByRole('dialog')).getByRole('alert')).toHaveTextContent(
      'Un formulaire modifié, sous cette fenêtre, attend ta réponse : ferme la fenêtre pour y répondre, puis rouvre le projet.',
    );
  });

  it('refusée pendant une réponse en cours, la fenêtre reste ouverte (la coque avertit)', async () => {
    refus = 'reponse-en-cours';
    const onClose = await ouvrir();
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la conversation Devis cuisine' })); });
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.queryByText(/Un formulaire modifié/)).toBeNull();
  });
});
