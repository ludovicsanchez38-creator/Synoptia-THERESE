import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useDemoStore } from '../../stores/demoStore';
import { ProjectSyncSection } from './ProjectSyncSection';

const api = vi.hoisted(() => ({
  etatSync: vi.fn(), definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
}));
vi.mock('../../services/api', () => api);

function attente<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((oui, non) => { resolve = oui; reject = non; });
  return { promise, resolve, reject };
}
const etat = (id: string) => ({ racine: `/Documents/${id}`, generation: 1, dernier_plan: null });
const plan = (id: string) => ({
  id: `plan-${id}`, etat: 'propose', generation_racine: 1,
  nb_indexer: 1, nb_reindexer: 0, nb_retirer: 0, nb_conflits: 0, nb_inchanges: 0,
  created_at: '2026-09-22T10:00:00Z',
  operations: [{ id: `op-${id}`, type: 'indexer', chemin: `/Documents/${id}/fichier-${id}.pdf`,
    etat: 'a_faire', erreur: null, attempt_count: 0, last_attempt_at: null }],
});

beforeEach(() => {
  Object.values(api).forEach((mock) => mock.mockReset());
  useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  api.etatSync.mockImplementation((id: string) => Promise.resolve(etat(id)));
  api.preparerPlanSync.mockImplementation((id: string) => Promise.resolve(plan(id)));
  api.appliquerPlanSync.mockResolvedValue(undefined);
  api.journalSync.mockResolvedValue({ operations: [] });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  useDemoStore.setState({ enabled: false, replacementMap: new Map() });
});

async function monterPlanA() {
  const vue = render(<ProjectSyncSection projectId="A" />);
  await act(async () => {});
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Préparer la synchronisation' })); });
  return vue;
}

describe('la synchronisation reste dans le contexte de son projet', () => {
  it('ignore un plan de A terminé après ouverture de B, sans relire A ni proposer son application', async () => {
    const ancien = attente<ReturnType<typeof plan>>();
    api.preparerPlanSync.mockReturnValueOnce(ancien.promise);
    const vue = render(<ProjectSyncSection projectId="A" />);
    await act(async () => {});
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la synchronisation' }));
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    await act(async () => { ancien.resolve(plan('A')); });

    expect(screen.getByText('/Documents/B')).toBeInTheDocument();
    expect(screen.queryByTestId('sync-plan')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Appliquer' })).toBeNull();
    expect(api.etatSync.mock.calls.map(([id]) => id)).toEqual(['A', 'B']);
    expect(api.appliquerPlanSync).not.toHaveBeenCalled();
  });

  it('retire le plan déjà montré dans A dès que B est ouvert', async () => {
    const vue = render(<ProjectSyncSection projectId="A" />);
    await act(async () => {});
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Préparer la synchronisation' })); });
    expect(screen.getByTestId('sync-plan')).toHaveTextContent('fichier-A.pdf');
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });

    expect(screen.getByText('/Documents/B')).toBeInTheDocument();
    expect(screen.queryByTestId('sync-plan')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Appliquer' })).toBeNull();
    expect(api.appliquerPlanSync).not.toHaveBeenCalled();
  });

  it('ne réutilise pas le contexte de A après un aller-retour A, B, A', async () => {
    const ancien = attente<ReturnType<typeof plan>>();
    api.preparerPlanSync.mockReturnValueOnce(ancien.promise);
    const vue = render(<ProjectSyncSection projectId="A" />);
    await act(async () => {});
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la synchronisation' }));
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="A" />); });
    await act(async () => { ancien.resolve(plan('A')); });
    expect(screen.getByText('/Documents/A')).toBeInTheDocument();
    expect(screen.queryByTestId('sync-plan')).toBeNull();
    expect(api.etatSync.mock.calls.map(([id]) => id)).toEqual(['A', 'B', 'A']);
  });

  it.each([false, true])('ignore l’attache tardive de A, échec=%s, sans libérer l’action en cours dans B', async (echec) => {
    const ancien = attente<void>();
    api.definirRacineSync.mockReturnValueOnce(ancien.promise);
    api.etatSync.mockImplementation((id: string) => Promise.resolve(id === 'A'
      ? { racine: null, generation: null, dernier_plan: null } : etat(id)));
    const vue = render(<ProjectSyncSection projectId="A" />);
    await act(async () => {});
    fireEvent.change(screen.getByLabelText('Chemin du dossier à synchroniser'), { target: { value: '/Documents/A' } });
    fireEvent.click(screen.getByRole('button', { name: 'Attacher' }));
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    api.preparerPlanSync.mockReturnValueOnce(new Promise(() => {}));
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la synchronisation' }));
    await act(async () => { if (echec) ancien.reject(new Error('Erreur ancienne A')); else ancien.resolve(); });
    expect(screen.getByText('/Documents/B')).toBeInTheDocument();
    expect(screen.queryByText('Erreur ancienne A')).toBeNull();
    expect(screen.getByRole('button', { name: 'Délier le dossier' })).toBeDisabled();
    expect(api.etatSync.mock.calls.map(([id]) => id)).toEqual(['A', 'B']);
  });

  it.each([false, true])('ignore la déliaison tardive de A, échec=%s', async (echec) => {
    const ancien = attente<void>();
    api.retirerRacineSync.mockReturnValueOnce(ancien.promise);
    const vue = render(<ProjectSyncSection projectId="A" />);
    await act(async () => {});
    fireEvent.click(screen.getByRole('button', { name: 'Délier le dossier' }));
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    await act(async () => { if (echec) ancien.reject(new Error('Erreur ancienne A')); else ancien.resolve(); });
    expect(screen.getByText('/Documents/B')).toBeInTheDocument();
    expect(screen.queryByTestId('sync-info')).toBeNull();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(api.etatSync.mock.calls.map(([id]) => id)).toEqual(['A', 'B']);
  });

  it('ne démarre pas le sondage après une application achevée dans un projet quitté', async () => {
    vi.useFakeTimers();
    const ancien = attente<void>();
    api.appliquerPlanSync.mockReturnValueOnce(ancien.promise);
    const vue = await monterPlanA();
    fireEvent.click(screen.getByRole('button', { name: 'Appliquer' }));
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    await act(async () => { ancien.resolve(); await vi.advanceTimersByTimeAsync(5000); });
    expect(screen.getByText('/Documents/B')).toBeInTheDocument();
    expect(api.etatSync.mock.calls.map(([id]) => id)).toEqual(['A', 'A', 'B']);
    expect(api.journalSync).not.toHaveBeenCalled();
    expect(api.appliquerPlanSync).toHaveBeenCalledExactlyOnceWith('A', 'plan-A');
  });

  it('ignore un sondage déjà parti de A et ne lance pas de lectures superposées', async () => {
    vi.useFakeTimers();
    const terminal = { ...etat('A'), dernier_plan: { ...plan('A'), etat: 'applique' } };
    const ancien = attente<typeof terminal>();
    const vue = await monterPlanA();
    api.etatSync.mockReturnValueOnce(ancien.promise);
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Appliquer' })); });
    await act(async () => { await vi.advanceTimersByTimeAsync(4000); });
    expect(api.etatSync).toHaveBeenCalledTimes(3);
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    await act(async () => { ancien.resolve(terminal); await vi.advanceTimersByTimeAsync(3000); });
    expect(screen.getByText('/Documents/B')).toBeInTheDocument();
    expect(api.etatSync.mock.calls.map(([id]) => id)).toEqual(['A', 'A', 'A', 'B']);
    expect(api.journalSync).not.toHaveBeenCalled();
    expect(screen.queryByTestId('sync-plan')).toBeNull();
  });

  it('ignore le journal de A reçu après ouverture de B', async () => {
    vi.useFakeTimers();
    const ancien = attente<{ operations: ReturnType<typeof plan>['operations'] }>();
    api.journalSync.mockReturnValueOnce(ancien.promise);
    const vue = await monterPlanA();
    api.etatSync.mockResolvedValueOnce({ ...etat('A'), dernier_plan: { ...plan('A'), etat: 'applique' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Appliquer' })); });
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(api.journalSync).toHaveBeenCalledExactlyOnceWith('A');
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    await act(async () => { ancien.resolve({ operations: plan('A').operations }); });
    expect(screen.getByText('/Documents/B')).toBeInTheDocument();
    expect(screen.queryByTestId('sync-journal')).toBeNull();
  });

  it('efface chemin, information et erreur du projet précédent', async () => {
    api.etatSync.mockResolvedValue({ racine: null, generation: null, dernier_plan: null });
    const vue = render(<ProjectSyncSection projectId="A" />);
    await act(async () => {});
    fireEvent.change(screen.getByLabelText('Chemin du dossier à synchroniser'), { target: { value: '/Documents/A' } });
    api.definirRacineSync.mockRejectedValueOnce(new Error('Erreur propre à A'));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Attacher' })); });
    expect(screen.getByRole('alert')).toHaveTextContent('Erreur propre à A');
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="B" />); });
    expect(screen.getByLabelText('Chemin du dossier à synchroniser')).toHaveValue('');
    expect(screen.queryByRole('alert')).toBeNull();
    api.etatSync.mockResolvedValue(etat('C'));
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="C" />); });
    api.retirerRacineSync.mockResolvedValueOnce(undefined);
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Délier le dossier' })); });
    expect(screen.getByTestId('sync-info')).toBeInTheDocument();
    await act(async () => { vue.rerender(<ProjectSyncSection projectId="D" />); });
    expect(screen.queryByTestId('sync-info')).toBeNull();
  });

  it('utilise le masque local fourni sans peupler ni modifier le store global', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    const masqueLocal = (texte: string) => texte.replaceAll('A', 'Projet masqué');
    render(<ProjectSyncSection projectId="A" maskDisplayText={masqueLocal} />);
    await act(async () => {});
    expect(screen.getByText('/Documents/Projet masqué')).toBeInTheDocument();
    expect(screen.queryByText('/Documents/A')).toBeNull();
    expect(useDemoStore.getState().replacementMap.size).toBe(0);
    expect(screen.getByRole('button', { name: 'Délier le dossier' })).toBeDisabled();
  });
});
