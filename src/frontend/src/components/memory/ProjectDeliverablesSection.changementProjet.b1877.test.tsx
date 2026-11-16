import { act, fireEvent, render, screen } from '@testing-library/react';
import { useLayoutEffect } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DeliverableResponse } from '../../services/api/crm-extended';
import { ProjectDeliverablesSection } from './ProjectDeliverablesSection';

const api = vi.hoisted(() => ({ listDeliverables: vi.fn(), createDeliverable: vi.fn() }));
vi.mock('../../services/api/crm-extended', () => api);

function differe<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((ok, ko) => { resolve = ok; reject = ko; });
  return { promise, resolve, reject };
}

function livrable(projectId: string): DeliverableResponse {
  return {
    id: `livrable-${projectId}`, project_id: projectId, title: `Livrable ${projectId}`,
    description: null, status: 'a_faire', due_date: null, completed_at: null,
    created_at: '', updated_at: '',
  };
}

function ajouter(titre: string) {
  fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: titre } });
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
}

describe('B-1877 / B-1878 : les réponses restent dans leur ouverture de projet', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    api.listDeliverables.mockResolvedValue([]);
  });

  it.each(['succès', 'échec'])('une lecture de A terminée dans le layout de B reste ignorée (%s)', async (issue) => {
    // Piloter la continuation permet de viser exactement la fenêtre entre
    // les effets de layout et le nettoyage des effets passifs de React.
    let resoudre!: (liste: DeliverableResponse[]) => void;
    let rejeter!: () => void;
    let terminer!: () => void;
    const lectureA = {
      then(suite: typeof resoudre) { resoudre = suite; return this; },
      catch(suite: typeof rejeter) { rejeter = suite; return this; },
      finally(suite: typeof terminer) { terminer = suite; return this; },
    };
    const lectureB = differe<DeliverableResponse[]>();
    api.listDeliverables.mockReturnValueOnce(lectureA).mockReturnValueOnce(lectureB.promise);
    function Ouverture({ projectId }: { projectId: string }) {
      useLayoutEffect(() => {
        if (projectId === 'B') {
          if (issue === 'succès') resoudre([{ ...livrable('A'), title: 'Secret du projet A' }]);
          else rejeter();
          terminer();
        }
      }, [projectId]);
      return <ProjectDeliverablesSection projectId={projectId} />;
    }
    const vue = render(<Ouverture projectId="A" />);
    vue.rerender(<Ouverture projectId="B" />);

    expect(screen.queryByText('Secret du projet A'), 'la lecture tardive de A apparaît dans B').not.toBeInTheDocument();
    expect(screen.queryByRole('alert'), 'l’erreur de lecture de A apparaît dans B').not.toBeInTheDocument();
    await act(async () => { lectureB.resolve([livrable('B')]); });
    expect(screen.getByText('Livrable B')).toBeInTheDocument();
  });

  it.each(['lecture avant succès', 'succès avant lecture'])(
    'une création terminée après fermeture actualise la nouvelle fenêtre (%s)', async (ordre) => {
      const creation = differe<DeliverableResponse>();
      const lectureRetour = differe<DeliverableResponse[]>();
      api.createDeliverable.mockReturnValueOnce(creation.promise);
      api.listDeliverables.mockResolvedValueOnce([]).mockReturnValueOnce(lectureRetour.promise);
      const ancienne = render(<ProjectDeliverablesSection projectId="A" />);
      await screen.findByText('Aucun livrable pour ce projet.');
      ajouter('Livrable A');
      ancienne.unmount();
      render(<ProjectDeliverablesSection projectId="A" />);
      fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Saisie de la nouvelle fenêtre' } });
      if (ordre === 'lecture avant succès') await act(async () => { lectureRetour.resolve([]); });
      api.listDeliverables.mockResolvedValue([livrable('A')]);

      await act(async () => { creation.resolve(livrable('A')); });
      if (ordre === 'succès avant lecture') await act(async () => { lectureRetour.resolve([]); });

      expect(screen.queryByText('Livrable A'), 'la création réussie reste invisible après réouverture').toBeInTheDocument();
      expect(screen.getAllByText('Livrable A')).toHaveLength(1);
      expect(screen.queryByText('Aucun livrable pour ce projet.')).not.toBeInTheDocument();
      expect(screen.getByLabelText('Nouveau livrable')).toHaveValue('Saisie de la nouvelle fenêtre');
    },
  );

  it('le premier DOM de B ne contient ni les livrables ni la saisie de A', async () => {
    const lectureB = differe<DeliverableResponse[]>();
    api.listDeliverables.mockResolvedValueOnce([livrable('A')]).mockReturnValueOnce(lectureB.promise);
    const observations: { projet: string; livrableA: boolean; saisie: string }[] = [];
    function Ouverture({ projectId }: { projectId: string }) {
      useLayoutEffect(() => {
        observations.push({
          projet: projectId,
          livrableA: screen.queryByText('Livrable A') !== null,
          saisie: (screen.getByLabelText('Nouveau livrable') as HTMLInputElement).value,
        });
      }, [projectId]);
      return <ProjectDeliverablesSection projectId={projectId} />;
    }
    const vue = render(<Ouverture projectId="A" />);
    await screen.findByText('Livrable A');
    fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Saisie de A' } });

    vue.rerender(<Ouverture projectId="B" />);

    expect(observations.find(({ projet }) => projet === 'B'), 'le premier DOM de B montre encore A')
      .toEqual({ projet: 'B', livrableA: false, saisie: '' });
    await act(async () => { lectureB.resolve([livrable('B')]); });
    expect(screen.getByText('Livrable B')).toBeInTheDocument();
  });

  it.each(['création avant lecture', 'lecture avant création'])(
    'un ajout de A ne rejoint jamais B, même après la fusion (%s)', async (ordre) => {
      const creationA = differe<DeliverableResponse>();
      const lectureB = differe<DeliverableResponse[]>();
      api.createDeliverable.mockReturnValueOnce(creationA.promise);
      api.listDeliverables.mockResolvedValueOnce([]).mockReturnValueOnce(lectureB.promise);
      const vue = render(<ProjectDeliverablesSection projectId="A" />);
      await screen.findByText('Aucun livrable pour ce projet.');
      ajouter('Livrable A');
      expect(api.createDeliverable).toHaveBeenCalledWith({ project_id: 'A', title: 'Livrable A', status: 'a_faire' });

      vue.rerender(<ProjectDeliverablesSection projectId="B" />);
      fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Saisie de B' } });
      if (ordre === 'création avant lecture') {
        await act(async () => { creationA.resolve(livrable('A')); });
        expect(screen.queryByText('Livrable A')).not.toBeInTheDocument();
        await act(async () => { lectureB.resolve([livrable('B')]); });
      } else {
        await act(async () => { lectureB.resolve([livrable('B')]); });
        await act(async () => { creationA.resolve(livrable('A')); });
      }
      expect(screen.queryByText('Livrable A')).not.toBeInTheDocument();
      expect(screen.getByText('Livrable B')).toBeInTheDocument();
      expect(screen.getByLabelText('Nouveau livrable')).toHaveValue('Saisie de B');
    },
  );

  it.each(['succès', 'échec'])('une réponse de A (%s) laisse la création de B en cours', async (resultat) => {
    const creationA = differe<DeliverableResponse>();
    const creationB = differe<DeliverableResponse>();
    api.createDeliverable.mockReturnValueOnce(creationA.promise).mockReturnValueOnce(creationB.promise);
    const vue = render(<ProjectDeliverablesSection projectId="A" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    ajouter('Livrable A');
    vue.rerender(<ProjectDeliverablesSection projectId="B" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    expect(screen.getByLabelText('Nouveau livrable')).toHaveValue('');
    ajouter('Livrable B');
    expect(api.createDeliverable).toHaveBeenCalledTimes(2);
    await act(async () => {
      if (resultat === 'succès') creationA.resolve(livrable('A'));
      else creationA.reject(new Error('Échec du projet A'));
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ajouter le livrable' })).toBeDisabled();
    expect(screen.getByLabelText('Nouveau livrable')).toHaveValue('Livrable B');
    expect(screen.queryByText('Livrable A')).not.toBeInTheDocument();
    await act(async () => { creationB.resolve(livrable('B')); });
    expect(screen.getByText('Livrable B')).toBeInTheDocument();
  });

  it('un retour à A ne réactive pas la réponse de sa précédente ouverture', async () => {
    const creationA = differe<DeliverableResponse>();
    api.createDeliverable.mockReturnValueOnce(creationA.promise);
    const vue = render(<ProjectDeliverablesSection projectId="A" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    ajouter('Livrable A');
    vue.rerender(<ProjectDeliverablesSection projectId="B" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    vue.rerender(<ProjectDeliverablesSection projectId="A" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    await act(async () => { creationA.resolve(livrable('A')); });
    expect(screen.queryByText('Livrable A')).not.toBeInTheDocument();
  });

  it.each(['lecture avant succès', 'succès avant lecture'])(
    'une création ancienne de A déclenche une relecture fidèle au retour (%s)', async (ordre) => {
      const creationA = differe<DeliverableResponse>();
      const lectureRetour = differe<DeliverableResponse[]>();
      api.createDeliverable.mockReturnValueOnce(creationA.promise);
      api.listDeliverables.mockResolvedValueOnce([]).mockResolvedValueOnce([])
        .mockReturnValueOnce(lectureRetour.promise);
      const vue = render(<ProjectDeliverablesSection projectId="A" />);
      await screen.findByText('Aucun livrable pour ce projet.');
      ajouter('Livrable A');
      vue.rerender(<ProjectDeliverablesSection projectId="B" />);
      await screen.findByText('Aucun livrable pour ce projet.');
      vue.rerender(<ProjectDeliverablesSection projectId="A" />);
      fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Nouvelle saisie de A' } });
      if (ordre === 'lecture avant succès') await act(async () => { lectureRetour.resolve([]); });

      // Le serveur a enregistré l'ajout ; la nouvelle lecture le voit.
      api.listDeliverables.mockResolvedValue([livrable('A')]);
      await act(async () => { creationA.resolve(livrable('A')); });
      if (ordre === 'succès avant lecture') await act(async () => { lectureRetour.resolve([]); });

      expect(screen.queryByText('Livrable A'), 'la création réussie reste invisible après A/B/A').toBeInTheDocument();
      expect(screen.queryByText('Aucun livrable pour ce projet.')).not.toBeInTheDocument();
      expect(screen.getAllByText('Livrable A')).toHaveLength(1);
      expect(screen.getByLabelText('Nouveau livrable')).toHaveValue('Nouvelle saisie de A');
      expect(api.listDeliverables).toHaveBeenLastCalledWith({ project_id: 'A' });
    },
  );

  it('une création ancienne de A laisse le nouvel ajout de A en cours', async () => {
    const ancienne = differe<DeliverableResponse>();
    const nouvelle = differe<DeliverableResponse>();
    api.createDeliverable.mockReturnValueOnce(ancienne.promise).mockReturnValueOnce(nouvelle.promise);
    const vue = render(<ProjectDeliverablesSection projectId="A" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    ajouter('Livrable A');
    vue.rerender(<ProjectDeliverablesSection projectId="B" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    vue.rerender(<ProjectDeliverablesSection projectId="A" />);
    await screen.findByText('Aucun livrable pour ce projet.');
    ajouter('Nouvel ajout de A');
    api.listDeliverables.mockResolvedValue([livrable('A')]);

    await act(async () => { ancienne.resolve(livrable('A')); });

    expect(screen.queryByText('Livrable A'), 'la création réussie reste invisible après A/B/A').toBeInTheDocument();
    expect(screen.getByLabelText('Nouveau livrable')).toHaveValue('Nouvel ajout de A');
    expect(screen.getByRole('button', { name: 'Ajouter le livrable' })).toBeDisabled();
    await act(async () => { nouvelle.resolve({ ...livrable('A'), id: 'nouveau-A', title: 'Nouvel ajout de A' }); });
    expect(screen.getAllByText('Livrable A')).toHaveLength(1);
    expect(screen.getByText('Nouvel ajout de A')).toBeInTheDocument();
  });
});
