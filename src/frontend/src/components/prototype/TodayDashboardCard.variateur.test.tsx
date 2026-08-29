/**
 * Le variateur du brief du jour (plan du 29/08/2026).
 *
 * Trois mots dans l'en-tête règlent combien de lignes le brief développe.
 * Rien ne disparaît : le reste est replié, et le repli annonce les retards.
 *
 * Ce que ces tests garantissent, et pourquoi :
 *  - le défaut est le comportement d'aujourd'hui (personne ne voit de
 *    changement sans avoir fait un geste) ;
 *  - le sous-titre continue de compter le TOTAL, jamais les lignes visibles ;
 *  - aucun retard ne disparaît en silence ;
 *  - la valeur meurt avec la journée civile du backend, pas avec un
 *    `new Date()` du navigateur (leçon BUG-125).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DashboardTask, TodayDashboard } from '../../services/api/dashboard';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { TodayDashboardCard } from './TodayDashboardCard';

const JOUR = '2026-07-13';

function tache(index: number, enRetard: boolean): DashboardTask {
  return {
    id: `t${index}`,
    title: `Tâche ${index}`,
    status: 'todo',
    priority: 'high',
    due_date: enRetard ? '2026-07-01' : '2026-07-20',
    project_id: null,
  };
}

/** `nbRetards` tâches en retard, puis des tâches à venir, pour `total` lignes. */
function dashboard(total: number, nbRetards: number, date = JOUR): TodayDashboard {
  const taches = Array.from({ length: total }, (_, i) => tache(i + 1, i < nbRetards));
  return {
    date,
    events: [],
    urgent_tasks: taches,
    due_follow_ups: [],
    overdue_invoices: [],
    stale_prospects: [],
    summary: {
      events_count: 0, tasks_count: total, follow_ups_count: 0,
      invoices_count: 0, prospects_count: 0,
    },
  };
}

function afficher(data: TodayDashboard) {
  return render(
    <TodayDashboardCard
      resource={{ status: 'ready', error: null, data }}
      onRetry={vi.fn()}
      onOpenView={vi.fn()}
    />,
  );
}

function lignesVisibles(): number {
  return screen.getAllByText(/^Tâche \d+$/).length;
}

describe('Variateur du brief - le geste', () => {
  beforeEach(() => {
    installLocalStorageStub();
  });

  it("garde le comportement d'aujourd'hui par défaut : six lignes, le reste replié", () => {
    afficher(dashboard(9, 0));

    expect(lignesVisibles()).toBe(6);
    expect(screen.getByRole('button', { name: /Voir les 3 autres éléments/ })).toBeInTheDocument();
    // Le sous-titre compte le total, pas les lignes visibles.
    expect(screen.getByText('9 éléments issus de tes données')).toBeInTheDocument();
  });

  it('propose trois mots écrits, pas trois pastilles muettes', () => {
    afficher(dashboard(9, 0));

    const groupe = screen.getByRole('radiogroup', { name: /montre-moi/i });
    expect(groupe).toBeInTheDocument();
    for (const mot of ['tout', "l'essentiel", 'le minimum']) {
      expect(screen.getByRole('radio', { name: mot })).toBeInTheDocument();
    }
    expect(screen.getByRole('radio', { name: "l'essentiel" })).toBeChecked();
  });

  it('« le minimum » développe deux lignes et replie le reste', () => {
    afficher(dashboard(9, 0));

    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    expect(lignesVisibles()).toBe(2);
    expect(screen.getByRole('button', { name: /Voir les 7 autres éléments/ })).toBeInTheDocument();
    expect(screen.getByText('9 éléments issus de tes données')).toBeInTheDocument();
  });

  it('« tout » développe la liste entière et retire le repli', () => {
    afficher(dashboard(9, 0));

    fireEvent.click(screen.getByRole('radio', { name: 'tout' }));

    expect(lignesVisibles()).toBe(9);
    expect(screen.queryByRole('button', { name: /autres éléments/ })).not.toBeInTheDocument();
  });
});

describe('Variateur du brief - aucun retard ne disparaît en silence', () => {
  beforeEach(() => {
    installLocalStorageStub();
  });

  it('annonce le nombre de retards repliés', () => {
    afficher(dashboard(9, 4));

    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    // 4 en retard, 2 développés : 2 retards partent dans le repli, et le
    // bouton le dit.
    expect(
      screen.getByRole('button', { name: /Voir les 7 autres éléments, dont 2 en retard/ }),
    ).toBeInTheDocument();
  });

  it('ne parle pas de retard quand le repli n’en contient aucun', () => {
    afficher(dashboard(9, 2));

    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    const bouton = screen.getByRole('button', { name: /autres éléments/ });
    expect(bouton).toHaveTextContent('Voir les 7 autres éléments');
    expect(bouton).not.toHaveTextContent('en retard');
  });
});

describe('Variateur du brief - la valeur meurt avec la journée', () => {
  beforeEach(() => {
    installLocalStorageStub();
  });

  it('retrouve le réglage tant que le backend annonce le même jour', () => {
    const { unmount } = afficher(dashboard(9, 0));
    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));
    unmount();

    afficher(dashboard(9, 0));

    expect(screen.getByRole('radio', { name: 'le minimum' })).toBeChecked();
    expect(lignesVisibles()).toBe(2);
  });

  it('repart du défaut dès que le backend annonce un autre jour', () => {
    const { unmount } = afficher(dashboard(9, 0));
    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));
    unmount();

    afficher(dashboard(9, 0, '2026-07-14'));

    expect(screen.getByRole('radio', { name: "l'essentiel" })).toBeChecked();
    expect(lignesVisibles()).toBe(6);
  });

  it('reste utilisable quand le navigateur refuse le stockage', () => {
    // Fenêtre privée, données de site bloquées, capture de vignette : l'accès
    // lui-même jette. Le variateur doit servir pour la séance sans planter.
    const refus = () => {
      throw new Error('stockage refusé');
    };
    vi.mocked(localStorage.getItem).mockImplementation(refus);
    vi.mocked(localStorage.setItem).mockImplementation(refus);
    vi.mocked(localStorage.key).mockImplementation(refus);

    afficher(dashboard(9, 0));
    expect(lignesVisibles()).toBe(6);
    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));
    expect(lignesVisibles()).toBe(2);
  });

  it("n'accumule pas une valeur par jour : les autres jours sont oubliés", () => {
    const store = installLocalStorageStub();
    store.set('therese.brief.variateur.2026-07-10', 'minimum');
    store.set('therese.brief.variateur.2026-07-11', 'tout');
    store.set('un.autre.reglage', 'intact');

    afficher(dashboard(9, 0));

    expect([...store.keys()].filter((c) => c.startsWith('therese.brief.variateur.'))).toEqual([]);
    // Ce qui n'appartient pas au variateur n'est pas touché.
    expect(store.get('un.autre.reglage')).toBe('intact');
  });

  it("choisir un réglage l'emporte sur une expansion déjà faite", () => {
    afficher(dashboard(9, 0));

    fireEvent.click(screen.getByRole('button', { name: /Voir les 3 autres éléments/ }));
    expect(lignesVisibles()).toBe(9);

    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    // Sans quoi le geste n'aurait aucun effet visible, et le contrôle
    // mentirait : c'est exactement la pastille placebo qu'on a refusée.
    expect(lignesVisibles()).toBe(2);
  });

  it("re-choisir le réglage déjà actif referme une expansion", () => {
    // Une radio déjà cochée n'émet pas `change`. Sans garde, le mot sur lequel
    // on clique pour « revenir à l'essentiel » ne fait rien : un contrôle
    // visiblement actif et sans effet, exactement la pastille placebo refusée.
    afficher(dashboard(9, 0));

    fireEvent.click(screen.getByRole('button', { name: /Voir les 3 autres éléments/ }));
    expect(lignesVisibles()).toBe(9);

    fireEvent.click(screen.getByRole('radio', { name: "l'essentiel" }));

    expect(lignesVisibles()).toBe(6);
  });

  it('« Voir les autres » est une expansion de séance, il ne change pas le réglage', () => {
    const { unmount } = afficher(dashboard(9, 0));

    fireEvent.click(screen.getByRole('button', { name: /Voir les 3 autres éléments/ }));
    expect(lignesVisibles()).toBe(9);
    // Le réglage n'a pas bougé.
    expect(screen.getByRole('radio', { name: "l'essentiel" })).toBeChecked();
    unmount();

    afficher(dashboard(9, 0));
    expect(lignesVisibles()).toBe(6);
  });
});

describe("Variateur du brief - rien ne sort de l'écran", () => {
  beforeEach(() => {
    installLocalStorageStub();
    vi.mocked(fetch).mockClear();
  });

  it("ne passe la valeur à aucun des rappels sortants de la carte", () => {
    // La liste blanche du test d'architecture exempte CETTE carte, puisqu'elle
    // détient la valeur. C'est donc ici, et nulle part ailleurs, qu'elle
    // pourrait la faire sortir : par un rappel remontant à la coque.
    const rappels = {
      onRetry: vi.fn(),
      onOpenView: vi.fn(),
      onOpenItem: vi.fn(),
      onSetupEmail: vi.fn(),
    };
    render(
      <TodayDashboardCard resource={{ status: 'ready', error: null, data: dashboard(9, 2) }} {...rappels} />,
    );

    for (const mot of ['tout', 'le minimum', "l'essentiel"]) {
      fireEvent.click(screen.getByRole('radio', { name: mot }));
    }
    fireEvent.click(screen.getByRole('button', { name: /autres éléments/ }));

    for (const rappel of Object.values(rappels)) {
      expect(rappel).not.toHaveBeenCalled();
    }

    // Et quand un rappel part pour une vraie raison, il ne porte pas la valeur.
    // Il faut emprunter TOUTES les sorties de la carte, pas seulement celle
    // qu'on a en tête : la première version de ce test ne cliquait pas le
    // bouton Agenda, et un sabotage qui faisait fuir la valeur par là passait.
    fireEvent.click(screen.getAllByText(/^Tâche \d+$/)[0]);
    fireEvent.click(screen.getByRole('button', { name: /Agenda/ }));
    const argumentsSortis = JSON.stringify([
      rappels.onRetry.mock.calls,
      rappels.onOpenView.mock.calls,
      rappels.onOpenItem.mock.calls,
      rappels.onSetupEmail.mock.calls,
    ]);
    for (const valeur of ['tout', 'essentiel', 'minimum']) {
      expect(argumentsSortis).not.toContain(valeur);
    }
  });

  it("ne déclenche aucun appel réseau depuis la carte, quelle que soit la valeur choisie", () => {
    afficher(dashboard(9, 3));

    for (const mot of ['tout', 'le minimum', "l'essentiel"]) {
      fireEvent.click(screen.getByRole('radio', { name: mot }));
    }

    // La réduction est une projection d'affichage. Le backend continue de
    // servir la journée entière, et le chat continue de la lire par ses
    // outils : c'est ça, la non-interférence.
    expect(vi.mocked(fetch)).not.toHaveBeenCalled();
  });

  it("n'écrit la valeur nulle part ailleurs que sous sa propre clé datée", () => {
    const store = installLocalStorageStub();

    afficher(dashboard(9, 0));
    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    expect([...store.keys()]).toEqual(['therese.brief.variateur.2026-07-13']);
  });
});

describe('Variateur du brief - aucun mot sans effet (revue Soso, P1)', () => {
  beforeEach(() => {
    installLocalStorageStub();
  });

  it("n'offre que les mots qui changent quelque chose", () => {
    // Avec 5 éléments, « tout » et « l'essentiel » afficheraient les mêmes 5
    // lignes : deux commandes identiques, donc une placebo. On n'en propose
    // qu'une.
    afficher(dashboard(5, 0));

    expect(screen.queryByRole('radio', { name: 'tout' })).not.toBeInTheDocument();
    expect(screen.getByRole('radio', { name: "l'essentiel" })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'le minimum' })).toBeInTheDocument();
  });

  it('offre les trois mots dès que les trois diffèrent', () => {
    afficher(dashboard(7, 0));

    for (const mot of ['tout', "l'essentiel", 'le minimum']) {
      expect(screen.getByRole('radio', { name: mot })).toBeInTheDocument();
    }
  });

  it('disparaît quand il ne resterait qu’un seul mot utile', () => {
    afficher(dashboard(2, 0));

    expect(screen.queryByRole('radiogroup')).not.toBeInTheDocument();
  });

  it('reste cohérent quand le réglage stocké n’est plus proposé', () => {
    const store = installLocalStorageStub();
    store.set('therese.brief.variateur.2026-07-13', 'tout');

    // « tout » n'est pas offert à 5 éléments, mais il donne le même résultat
    // que « l'essentiel » : c'est ce mot-là qui doit être coché.
    afficher(dashboard(5, 0));

    expect(screen.getByRole('radio', { name: "l'essentiel" })).toBeChecked();
    expect(lignesVisibles()).toBe(5);
  });

  it("n'écrit qu'une fois par sélection", () => {
    installLocalStorageStub();
    const ecritures = vi.mocked(localStorage.setItem);
    ecritures.mockClear();

    afficher(dashboard(9, 0));
    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    expect(ecritures).toHaveBeenCalledTimes(1);
  });
});

describe('Variateur du brief - le chargement ne ment pas (revue Soso, P2)', () => {
  beforeEach(() => {
    installLocalStorageStub();
  });

  it("ne titre pas « Aucune priorité détectée » pendant qu'il relit", () => {
    render(
      <TodayDashboardCard
        resource={{ status: 'loading', error: null, data: null }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
      />,
    );

    expect(screen.queryByRole('heading', { name: 'Aucune priorité détectée' })).not.toBeInTheDocument();
  });

  it('retrouve son réglage après un aller-retour par le chargement', () => {
    const { rerender } = afficher(dashboard(9, 0));
    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    rerender(
      <TodayDashboardCard
        resource={{ status: 'loading', error: null, data: null }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
      />,
    );
    rerender(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard(9, 0) }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
      />,
    );

    expect(screen.getByRole('radio', { name: 'le minimum' })).toBeChecked();
    expect(lignesVisibles()).toBe(2);
  });

  it("change de jour sans remontage : le réglage repart du défaut", () => {
    const { rerender } = afficher(dashboard(9, 0));
    fireEvent.click(screen.getByRole('radio', { name: 'le minimum' }));

    rerender(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard(9, 0, '2026-07-14') }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
      />,
    );

    expect(screen.getByRole('radio', { name: "l'essentiel" })).toBeChecked();
    expect(lignesVisibles()).toBe(6);
  });
});

describe('Variateur du brief - le repli se lit en français', () => {
  beforeEach(() => {
    installLocalStorageStub();
  });

  it("ne dit pas « les 1 autre élément » quand il n'en reste qu'un", () => {
    afficher(dashboard(7, 0));

    const bouton = screen.getByRole('button', { name: /élément/ });
    expect(bouton).toHaveTextContent('Voir le dernier élément');
    expect(bouton).not.toHaveTextContent('les 1');
  });

  it('annonce le retard du dernier élément sans compter jusqu’à un', () => {
    // 7 éléments, 7 en retard : le seul replié est en retard.
    afficher(dashboard(7, 7));

    expect(screen.getByRole('button', { name: /élément/ })).toHaveTextContent(
      'Voir le dernier élément, en retard',
    );
  });
});
