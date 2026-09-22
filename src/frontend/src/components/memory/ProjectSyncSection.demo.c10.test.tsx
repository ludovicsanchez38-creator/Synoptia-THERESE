/** B-939 : une synchronisation masquée se consulte sans modifier ses données. */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useDemoStore } from '../../stores/demoStore';
import { ProjectSyncSection } from './ProjectSyncSection';

const api = vi.hoisted(() => ({
  etatSync: vi.fn(), definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
}));
vi.mock('../../services/api', () => api);

const RACINE = '/Dossiers/Victor Ruiz';
const RACINE_DEMO = '/Dossiers/Alexandre Moreau';
const PLAN = {
  id: 'plan-c10', etat: 'propose', generation_racine: 1,
  nb_indexer: 1, nb_reindexer: 0, nb_retirer: 0, nb_conflits: 0, nb_inchanges: 0,
  created_at: '2026-09-22T10:00:00Z',
  operations: [{
    id: 'operation-c10', type: 'indexer', chemin: `${RACINE}/Devis Victor Ruiz.pdf`,
    etat: 'a_faire', erreur: null, attempt_count: 0, last_attempt_at: null,
  }],
};

describe('B-939 : dossier synchronisé en lecture seule démo', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    useDemoStore.setState({
      enabled: true, replacementMap: new Map([['Victor Ruiz', 'Alexandre Moreau']]),
    });
    api.etatSync.mockResolvedValue({ racine: RACINE, generation: 1, dernier_plan: null });
    api.preparerPlanSync.mockResolvedValue(PLAN);
  });

  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('masque la racine et verrouille déliaison et préparation', async () => {
    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });
    expect(screen.getByText(RACINE_DEMO)).toBeInTheDocument();
    expect(screen.queryByText(RACINE)).toBeNull();
    expect(screen.getByText(/Désactive le mode démo/)).toBeInTheDocument();
    const delier = screen.getByRole('button', { name: 'Délier le dossier' });
    const preparer = screen.getByRole('button', { name: 'Préparer la synchronisation' });
    expect(delier).toBeDisabled();
    expect(preparer).toBeDisabled();
    fireEvent.click(delier);
    fireEvent.click(preparer);
    expect(api.retirerRacineSync).not.toHaveBeenCalled();
    expect(api.preparerPlanSync).not.toHaveBeenCalled();
  });

  it('sans dossier, verrouille le champ et l’attache', async () => {
    api.etatSync.mockResolvedValue({ racine: null, generation: null, dernier_plan: null });
    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });
    expect(screen.getByLabelText('Chemin du dossier à synchroniser')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Attacher' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Attacher' }));
    expect(api.definirRacineSync).not.toHaveBeenCalled();
  });

  it('masque un chemin déjà saisi sans jamais envoyer cet alias lors du retour en édition', async () => {
    useDemoStore.setState({ enabled: false });
    api.etatSync.mockResolvedValue({ racine: null, generation: null, dernier_plan: null });
    api.definirRacineSync.mockResolvedValue(undefined);
    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });
    const champ = screen.getByLabelText('Chemin du dossier à synchroniser');
    fireEvent.change(champ, { target: { value: RACINE } });
    await act(async () => { useDemoStore.setState({ enabled: true }); });
    expect(champ).toHaveValue(RACINE_DEMO);
    expect(champ).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Attacher' }));
    expect(api.definirRacineSync).not.toHaveBeenCalled();

    await act(async () => { useDemoStore.setState({ enabled: false }); });
    expect(champ).toHaveValue(RACINE);
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Attacher' })); });
    expect(api.definirRacineSync).toHaveBeenCalledWith('projet-c10', RACINE);
    expect(api.definirRacineSync).toHaveBeenCalledTimes(1);
  });

  it('masque les fichiers d’un plan déjà préparé et interdit son application après activation démo', async () => {
    useDemoStore.setState({ enabled: false });
    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Préparer la synchronisation' })); });
    expect(screen.getByTestId('sync-plan')).toHaveTextContent('Devis Victor Ruiz.pdf');
    await act(async () => { useDemoStore.setState({ enabled: true }); });
    expect(screen.getByTestId('sync-plan')).toHaveTextContent('Devis Alexandre Moreau.pdf');
    expect(screen.getByTestId('sync-plan')).not.toHaveTextContent('Victor Ruiz');
    const appliquer = screen.getByRole('button', { name: 'Appliquer' });
    expect(appliquer).toBeDisabled();
    fireEvent.click(appliquer);
    expect(api.appliquerPlanSync).not.toHaveBeenCalled();
  });

  it('masque aussi les noms présents dans une erreur déjà affichée', async () => {
    useDemoStore.setState({ enabled: false });
    api.preparerPlanSync.mockRejectedValue(new Error('Dossier Victor Ruiz inaccessible'));
    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Préparer la synchronisation' })); });
    await act(async () => { useDemoStore.setState({ enabled: true }); });
    expect(screen.getByRole('alert')).toHaveTextContent('Dossier Alexandre Moreau inaccessible');
    expect(screen.getByRole('alert')).not.toHaveTextContent('Victor Ruiz');
  });
});
