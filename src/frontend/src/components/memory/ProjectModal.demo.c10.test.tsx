/** B-939 : les données fictives de présentation ne remplacent jamais les données métier. */
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact, FileMetadata, Project } from '../../services/api';
import { buildReplacementMap, maskText } from '../../lib/demoMask';
import { useDemoMask } from '../../hooks/useDemoMask';
import { useDemoStore } from '../../stores/demoStore';
import { ProjectModal } from './ProjectModal';

const api = vi.hoisted(() => ({
  listContacts: vi.fn(), listProjectFiles: vi.fn(), etatSync: vi.fn(),
  updateProject: vi.fn(), createProject: vi.fn(), deleteProject: vi.fn(),
  deleteFile: vi.fn(), uploadProjectFile: vi.fn(),
  definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
}));
vi.mock('../../services/api', () => api);

// Toutes les données ci-dessous sont synthétiques ; aucun appel réseau réel.
const CONTACT: Contact = {
  id: 'contact-demo-c10', first_name: 'Victor', last_name: 'Ruiz',
  company: 'Entreprise Ardent', email: 'victor@example.invalid', phone: null,
  address: null, notes: null, tags: null, stage: 'prospect', score: 20,
  source: null, last_interaction: null,
  created_at: '2026-09-22T10:00:00Z', updated_at: '2026-09-22T10:00:00Z',
};
const PROJET: Project = {
  id: 'projet-demo-c10', name: 'Chantier Ardent c10',
  description: 'Projet préparé pour Victor Ruiz', contact_id: CONTACT.id,
  status: 'active', budget: 1200, notes: 'Relancer Entreprise Ardent', tags: ['Ruiz'],
  created_at: '2026-09-22T10:00:00Z', updated_at: '2026-09-22T10:00:00Z',
};
const FICHIER: FileMetadata = {
  id: 'fichier-demo-c10', name: 'Devis Victor Ruiz.pdf', extension: '.pdf',
  path: '/Dossiers/Victor Ruiz/Devis Victor Ruiz.pdf', size: 400,
  mime_type: 'application/pdf', chunk_count: 1, indexed_at: null,
  created_at: '2026-09-22T10:00:00Z',
};
const RACINE = '/Dossiers/Victor Ruiz/Chantier Ardent c10';
const REMPLACEMENTS = buildReplacementMap([CONTACT], [PROJET]);
const masquer = (texte: string) => maskText(texte, REMPLACEMENTS);

async function ouvrir(modeDemo: boolean) {
  useDemoStore.setState({ enabled: modeDemo, replacementMap: new Map(REMPLACEMENTS) });
  const masque = renderHook(() => useDemoMask());
  expect(masque.result.current.maskText(PROJET.name)).toBe(modeDemo ? masquer(PROJET.name) : PROJET.name);
  masque.unmount();
  await act(async () => {
    render(<ProjectModal isOpen onClose={vi.fn()} project={PROJET} />);
  });
  expect(api.listContacts).toHaveBeenCalledOnce();
  expect(api.listProjectFiles).toHaveBeenCalledWith(PROJET.id);
  expect(api.etatSync).toHaveBeenCalledWith(PROJET.id);
}

describe('B-939 : ouverture d’un projet en mode démonstration', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listContacts.mockResolvedValue([CONTACT]);
    api.listProjectFiles.mockResolvedValue({ files: [FICHIER], total: 1, truncated: false });
    api.etatSync.mockResolvedValue({ racine: RACINE, generation: 1, dernier_plan: null });
    api.updateProject.mockResolvedValue(PROJET);
    api.createProject.mockResolvedValue(PROJET);
    api.deleteProject.mockResolvedValue(undefined);
    api.deleteFile.mockResolvedValue(undefined);
    api.uploadProjectFile.mockResolvedValue(FICHIER);
    api.retirerRacineSync.mockResolvedValue(undefined);
    api.preparerPlanSync.mockResolvedValue({
      id: 'plan-demo-c10', etat: 'propose', nb_indexer: 1, nb_reindexer: 0,
      nb_retirer: 0, nb_inchanges: 0, nb_conflits: 0, operations: [],
    });
    api.appliquerPlanSync.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('garde les valeurs métier visibles quand le mode démo est désactivé', async () => {
    await ouvrir(false);
    expect(screen.getByRole('textbox', { name: /Nom du projet/ })).toHaveValue(PROJET.name);
    expect(screen.getByRole('textbox', { name: 'Description' })).toHaveValue(PROJET.description);
    expect(screen.getByRole('option', { name: 'Victor Ruiz (Entreprise Ardent)' })).toBeInTheDocument();
    expect(screen.getByText(FICHIER.name)).toBeInTheDocument();
    expect(screen.getByText(RACINE)).toBeInTheDocument();
  });

  it('masque aussi une ouverture à froid sans table de remplacements globale', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    await act(async () => { render(<ProjectModal isOpen onClose={vi.fn()} project={PROJET} />); });
    expect(screen.getByRole('textbox', { name: 'Description' })).toHaveValue(masquer(PROJET.description!));
    expect(screen.getByRole('textbox', { name: 'Notes' })).toHaveValue(masquer(PROJET.notes!));
    expect(screen.queryByText(FICHIER.name)).toBeNull();
    expect(screen.queryByText(RACINE)).toBeNull();
    expect(screen.getByText(masquer(RACINE))).toBeInTheDocument();
    // La fiche enrichit son masque local, sans écraser ceux des autres vues.
    expect(useDemoStore.getState().replacementMap.size).toBe(0);
  });

  it('ne dévoile pas les textes en attendant les contacts nécessaires au masque', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    api.listContacts.mockReturnValue(new Promise(() => {}));
    await act(async () => { render(<ProjectModal isOpen onClose={vi.fn()} project={PROJET} />); });
    expect(screen.getByRole('textbox', { name: 'Description' })).not.toHaveValue(PROJET.description);
    expect(screen.getByRole('textbox', { name: 'Notes' })).not.toHaveValue(PROJET.notes);
    expect(screen.queryByText(FICHIER.name)).toBeNull();
    expect(screen.queryByText(RACINE)).toBeNull();
  });

  it('montre les champs masqués en lecture seule avec un rappel pour désactiver le mode démo', async () => {
    await ouvrir(true);
    expect.soft(screen.queryAllByText(/désactiv.*(?:démo|démonstration)/i).length).toBeGreaterThan(0);
    for (const [libelle, original] of [
      [/Nom du projet/, PROJET.name],
      ['Description', PROJET.description],
      ['Notes', PROJET.notes],
      [/Tags/, 'Ruiz'],
    ] as const) {
      const champ = screen.queryByRole('textbox', { name: libelle });
      if (champ) {
        expect.soft(champ).not.toHaveValue(original);
        const lectureSeule = (champ as HTMLInputElement | HTMLTextAreaElement).readOnly;
        if (!lectureSeule) expect.soft(champ).toBeDisabled();
      }
    }
    expect(api.updateProject).not.toHaveBeenCalled();
  });

  it('masque les options de contacts en conservant leur identifiant métier', async () => {
    await ouvrir(true);
    expect.soft(screen.queryByRole('option', { name: /Victor Ruiz|Entreprise Ardent/ })).toBeNull();
    const option = screen.queryByRole('option', {
      name: masquer('Victor Ruiz (Entreprise Ardent)'),
    });
    expect.soft(option).toBeInTheDocument();
    if (option) {
      expect(option).toHaveValue(CONTACT.id);
      expect(screen.getByRole('combobox', { name: 'Contact associé' })).toBeDisabled();
    }
  });

  it('masque les noms de fichiers, les actions accessibles et la racine synchronisée', async () => {
    await ouvrir(true);
    expect.soft(screen.queryByText(FICHIER.name)).toBeNull();
    expect.soft(screen.queryByText(RACINE)).toBeNull();
    expect.soft(screen.queryByRole('button', { name: `Supprimer le fichier ${FICHIER.name}` })).toBeNull();
    expect.soft(screen.queryByTitle(`Supprimer le fichier ${FICHIER.name}`)).toBeNull();
    expect.soft(screen.queryByText(masquer(FICHIER.name))).toBeInTheDocument();
    expect.soft(screen.queryByText(masquer(RACINE))).toBeInTheDocument();
  });

  it('une confirmation déjà ouverte ne révèle plus le fichier et ne peut plus supprimer après activation démo', async () => {
    await ouvrir(false);
    fireEvent.click(screen.getByRole('button', { name: /Supprimer le fichier/ }));
    await act(async () => { useDemoStore.setState({ enabled: true }); });
    expect.soft(screen.queryByText(`Supprimer « ${FICHIER.name} » ?`)).toBeNull();
    expect(api.deleteFile).not.toHaveBeenCalled();
    const confirmer = screen.queryByRole('button', { name: 'Supprimer définitivement' });
    if (confirmer) await act(async () => { fireEvent.click(confirmer); });
    expect.soft(api.deleteFile).not.toHaveBeenCalled();
  });

  it('aucune action de la fiche ne crée de mutation API en mode démo', async () => {
    await ouvrir(true);
    // Toute action encore présentée doit être réellement désactivée. Les
    // actions retirées d’une fiche de consultation conviennent également.
    for (const nom of [
      'Mettre à jour', 'Supprimer', 'Supprimer', /Supprimer le fichier/,
      'Supprimer définitivement', 'Délier le dossier', /Préparer la synchronisation/, 'Appliquer',
    ]) {
      const bouton = screen.queryByRole('button', { name: nom });
      if (bouton) await act(async () => { fireEvent.click(bouton); });
    }
    const upload = document.querySelector<HTMLInputElement>('input[type=file]');
    if (upload) {
      expect.soft(upload).toBeDisabled();
      if (!upload.matches(':disabled')) {
        await act(async () => {
          fireEvent.change(upload, { target: { files: [new File(['synthétique'], 'test-c10.txt')] } });
        });
      }
    }
    for (const mutation of [
      api.createProject, api.updateProject, api.deleteProject, api.deleteFile,
      api.uploadProjectFile, api.definirRacineSync, api.retirerRacineSync,
      api.preparerPlanSync, api.appliquerPlanSync,
    ]) {
      expect.soft(mutation).not.toHaveBeenCalled();
    }
    expect(PROJET.name).toBe('Chantier Ardent c10');
    expect(CONTACT.first_name).toBe('Victor');
  });

  it('ne crée pas de projet depuis la modale de création en mode démo', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map(REMPLACEMENTS) });
    await act(async () => { render(<ProjectModal isOpen onClose={vi.fn()} />); });
    const nom = screen.queryByRole('textbox', { name: /Nom du projet/ });
    if (nom && !nom.matches(':disabled') && !(nom as HTMLInputElement).readOnly) {
      fireEvent.change(nom, { target: { value: 'Projet de test synthétique' } });
    }
    const creer = screen.queryByRole('button', { name: 'Créer' });
    if (creer) await act(async () => { fireEvent.click(creer); });
    expect(api.createProject).not.toHaveBeenCalled();
  });

  it('ne permet pas d’attacher un dossier depuis une fiche en mode démo', async () => {
    api.etatSync.mockResolvedValue({ racine: null, generation: null, dernier_plan: null });
    api.definirRacineSync.mockResolvedValue(undefined);
    await ouvrir(true);
    const chemin = screen.queryByLabelText('Chemin du dossier à synchroniser');
    if (chemin && !chemin.matches(':disabled') && !(chemin as HTMLInputElement).readOnly) {
      fireEvent.change(chemin, { target: { value: '/Dossiers/synthetique-c10' } });
    }
    const attacher = screen.queryByRole('button', { name: 'Attacher' });
    if (attacher) await act(async () => { fireEvent.click(attacher); });
    expect(api.definirRacineSync).not.toHaveBeenCalled();
  });

  it('retrouve l’édition réelle à la désactivation du mode démo, sans envoyer d’alias', async () => {
    await ouvrir(true);
    await act(async () => { useDemoStore.setState({ enabled: false }); });
    expect(screen.getByRole('textbox', { name: /Nom du projet/ })).toHaveValue(PROJET.name);
    expect(screen.getByRole('button', { name: 'Mettre à jour' })).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
    await waitFor(() => expect(api.updateProject).toHaveBeenCalledWith(PROJET.id, {
      name: PROJET.name, description: PROJET.description, contact_id: CONTACT.id,
      status: PROJET.status, budget: PROJET.budget, notes: PROJET.notes, tags: PROJET.tags,
    }));
    expect(api.updateProject).toHaveBeenCalledTimes(1);
    expect(JSON.stringify(api.updateProject.mock.calls)).not.toContain(masquer(PROJET.name));
  });
});
