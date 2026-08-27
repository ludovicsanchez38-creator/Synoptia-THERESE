/**
 * Le parcours « Dossier synchronisé » : attacher, préparer, appliquer.
 *
 * Le contrat montré à l'utilisateur : rien ne s'applique sans un plan
 * affiché, les conflits sont annoncés comme non exécutés, un échec de plan
 * (montage débranché) affiche l'erreur - jamais un plan vide de retrait.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  etatSync: vi.fn(),
  definirRacineSync: vi.fn(),
  retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(),
  appliquerPlanSync: vi.fn(),
  journalSync: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

import { ProjectSyncSection } from './ProjectSyncSection';

const PLAN = {
  id: 'plan-1', etat: 'propose', generation_racine: 1,
  nb_indexer: 3, nb_reindexer: 1, nb_retirer: 2, nb_conflits: 1, nb_inchanges: 5,
  created_at: '2026-08-24T00:00:00Z',
  operations: [
    { id: 'op-1', type: 'indexer', chemin: '/r/a.txt', etat: 'a_faire',
      erreur: null, attempt_count: 0, last_attempt_at: null },
  ],
};

describe('ProjectSyncSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.etatSync.mockResolvedValue({ racine: null, generation: null, dernier_plan: null });
  });

  it('attache un dossier puis affiche la racine', async () => {
    apiMocks.definirRacineSync.mockResolvedValue({ racine: '/r', generation: 1 });

    render(<ProjectSyncSection projectId="p-1" />);
    const champ = await screen.findByLabelText('Chemin du dossier à synchroniser');

    apiMocks.etatSync.mockResolvedValue({ racine: '/r', generation: 1, dernier_plan: null });
    fireEvent.change(champ, { target: { value: '/r' } });
    fireEvent.click(screen.getByRole('button', { name: 'Attacher' }));

    await waitFor(() => {
      expect(apiMocks.definirRacineSync).toHaveBeenCalledWith('p-1', '/r');
      expect(screen.getByText('/r')).toBeInTheDocument();
    });
  });

  it('montre le plan avant tout apply, conflits annoncés non exécutés', async () => {
    apiMocks.etatSync.mockResolvedValue({ racine: '/r', generation: 1, dernier_plan: null });
    apiMocks.preparerPlanSync.mockResolvedValue(PLAN);

    render(<ProjectSyncSection projectId="p-1" />);
    fireEvent.click(
      await screen.findByRole('button', { name: /Préparer la synchronisation/ }),
    );

    await waitFor(() => {
      expect(screen.getByTestId('sync-plan')).toHaveTextContent(
        '3 à indexer, 1 à réindexer, 2 à retirer, 5 inchangés',
      );
      expect(screen.getByTestId('sync-plan')).toHaveTextContent(
        '1 en conflit (non exécutés)',
      );
    });

    fireEvent.click(screen.getByRole('button', { name: /Appliquer/ }));
    await waitFor(() => {
      expect(apiMocks.appliquerPlanSync).toHaveBeenCalledWith('p-1', 'plan-1');
    });
  });

  it('un plan en échec affiche la cause, jamais un plan vide', async () => {
    apiMocks.etatSync.mockResolvedValue({ racine: '/r', generation: 1, dernier_plan: null });
    apiMocks.preparerPlanSync.mockRejectedValue(
      new Error('Aucun plan produit : racine introuvable'),
    );

    render(<ProjectSyncSection projectId="p-1" />);
    fireEvent.click(
      await screen.findByRole('button', { name: /Préparer la synchronisation/ }),
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('racine introuvable');
      expect(screen.queryByTestId('sync-plan')).not.toBeInTheDocument();
    });
  });
});

describe('ProjectSyncSection - le suivi d’apply ne ment jamais', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('le sondage s’arrête après cinq erreurs consécutives, avec un message', async () => {
    vi.useFakeTimers();
    apiMocks.etatSync.mockResolvedValueOnce({
      racine: '/r', generation: 1, dernier_plan: null, run: null,
    });
    apiMocks.preparerPlanSync.mockResolvedValue(PLAN);
    apiMocks.appliquerPlanSync.mockResolvedValue(undefined);

    render(<ProjectSyncSection projectId="p-1" />);
    await vi.waitFor(() => {
      expect(screen.getByRole('button', { name: /Préparer/ })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Préparer/ }));
    await vi.waitFor(() => {
      expect(screen.getByRole('button', { name: /Appliquer/ })).toBeInTheDocument();
    });

    apiMocks.etatSync.mockRejectedValue(new Error('backend muet'));
    fireEvent.click(screen.getByRole('button', { name: /Appliquer/ }));
    for (let i = 0; i < 6; i++) {
      await vi.advanceTimersByTimeAsync(1000);
    }

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Impossible de suivre la synchronisation',
    );
    vi.useRealTimers();
  });

  it('affiche le journal une fois la synchronisation terminée', async () => {
    vi.useFakeTimers();
    apiMocks.etatSync.mockResolvedValue({
      racine: '/r', generation: 1, dernier_plan: null, run: null,
    });
    apiMocks.preparerPlanSync.mockResolvedValue(PLAN);
    apiMocks.appliquerPlanSync.mockResolvedValue(undefined);
    apiMocks.journalSync.mockResolvedValue({
      operations: [
        { id: 'op-1', type: 'indexer', chemin: '/r/a.txt', etat: 'fait',
          erreur: null, attempt_count: 1, last_attempt_at: null },
      ],
    });

    render(<ProjectSyncSection projectId="p-1" />);
    await vi.waitFor(() => {
      expect(screen.getByRole('button', { name: /Préparer/ })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Préparer/ }));
    await vi.waitFor(() => {
      expect(screen.getByRole('button', { name: /Appliquer/ })).toBeInTheDocument();
    });

    apiMocks.etatSync.mockResolvedValue({
      racine: '/r', generation: 1,
      dernier_plan: { ...PLAN, etat: 'applique' }, run: { etat: 'done', progression: 1 },
    });
    fireEvent.click(screen.getByRole('button', { name: /Appliquer/ }));
    await vi.advanceTimersByTimeAsync(1000);
    await vi.waitFor(() => {
      expect(screen.getByTestId('sync-journal')).toHaveTextContent('a.txt');
    });
    vi.useRealTimers();
  });
});

// ---------------------------------------------------------------------------
// D4 et D5 (Dr_logic, 25 et 27/08) : ce que l'écran dit quand ça rate.
//
// « la synchro de dossier me donne un message peu explicite », puis « il y a
// un délai sur la synchronisation ? ». Le composant affichait `e.message`
// brut : « Délai de 30000 ms dépassé » est du jargon, et il ne dit ni ce qui
// s'est passé, ni quoi faire.
//
// Pire : quand le client abandonne, le serveur poursuit. La racine peut être
// posée alors que l'écran annonce un échec. Il faut donc relire l'état après
// un échec, sans quoi l'écran ment.
// ---------------------------------------------------------------------------

function erreurDeDelai(): Error {
  const e = new Error('Délai de 30000 ms dépassé');
  e.name = 'TimeoutError';
  return e;
}

describe('D4/D5 : un échec d’attache s’explique et relit l’état', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.etatSync.mockResolvedValue({
      racine: null, generation: null, dernier_plan: null, run: null,
    });
    apiMocks.journalSync.mockResolvedValue([]);
  });

  it('traduit le délai dépassé au lieu d’afficher le jargon', async () => {
    apiMocks.definirRacineSync.mockRejectedValue(erreurDeDelai());
    render(<ProjectSyncSection projectId="p1" />);
    await waitFor(() => expect(apiMocks.etatSync).toHaveBeenCalled());

    const champ = screen.getByPlaceholderText(/Documents/i);
    fireEvent.change(champ, { target: { value: 'D:\\site' } });
    fireEvent.click(screen.getByRole('button', { name: /attacher/i }));

    const message = await screen.findByRole('alert');
    expect(message.textContent).not.toContain('30000');
    expect(message.textContent?.toLowerCase()).toMatch(/temps|délai|long/);
    // Et il dit quoi faire.
    expect(message.textContent?.toLowerCase()).toMatch(/réessa|vérifi|patient/);
  });

  it('relit l’état après un échec — le serveur a pu réussir sans nous', async () => {
    apiMocks.definirRacineSync.mockRejectedValue(erreurDeDelai());
    render(<ProjectSyncSection projectId="p1" />);
    await waitFor(() => expect(apiMocks.etatSync).toHaveBeenCalled());
    const appelsAvant = apiMocks.etatSync.mock.calls.length;

    const champ = screen.getByPlaceholderText(/Documents/i);
    fireEvent.change(champ, { target: { value: 'D:\\site' } });
    fireEvent.click(screen.getByRole('button', { name: /attacher/i }));

    await waitFor(() =>
      expect(apiMocks.etatSync.mock.calls.length).toBeGreaterThan(appelsAvant)
    );
  });

  it('un refus du serveur garde son explication', async () => {
    const refus = new Error('Cette racine appartient déjà à un autre projet.');
    apiMocks.definirRacineSync.mockRejectedValue(refus);
    render(<ProjectSyncSection projectId="p1" />);
    await waitFor(() => expect(apiMocks.etatSync).toHaveBeenCalled());

    const champ = screen.getByPlaceholderText(/Documents/i);
    fireEvent.change(champ, { target: { value: 'D:\\site' } });
    fireEvent.click(screen.getByRole('button', { name: /attacher/i }));

    const message = await screen.findByRole('alert');
    expect(message.textContent).toContain('appartient déjà');
  });

  it('délier signale son échec au lieu de rester muet', async () => {
    apiMocks.etatSync.mockResolvedValue({
      racine: 'D:\\site', generation: 1, dernier_plan: null, run: null,
    });
    apiMocks.retirerRacineSync.mockRejectedValue(new Error('Le serveur a refusé.'));
    render(<ProjectSyncSection projectId="p1" />);
    await waitFor(() => expect(apiMocks.etatSync).toHaveBeenCalled());

    fireEvent.click(await screen.findByRole('button', { name: /Délier/i }));

    const message = await screen.findByRole('alert');
    expect(message.textContent).toContain('refusé');
  });
});
