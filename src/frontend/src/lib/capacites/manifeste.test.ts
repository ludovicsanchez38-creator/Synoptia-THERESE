/**
 * Manifeste de capacités — pilote « vues et navigation » (0.44).
 *
 * L'inventaire du 13/08 a établi que sept surfaces déclarent chacune, à la main,
 * ce que l'application sait faire, et qu'elles divergent déjà : la vue qui porte
 * l'indexation et le RAG était absente de la table du backend, donc introuvable
 * par `{action: ouvrir …}` comme par `/aide`.
 *
 * Ces tests décrivent le contrat du manifeste, pas son implémentation. Ils
 * portent sur le PILOTE : les vues et les actions de navigation, le sous-ensemble
 * le mieux délimité.
 *
 * Le manifeste ne remplace aucun registre. Il les RELIE : chaque `binding`
 * référence un identifiant qui existe déjà ailleurs, et c'est cette référence
 * typée qui rend les vérifications mécaniques possibles.
 */
import { describe, expect, it } from 'vitest';

import { APP_ACTIONS as ACTIONS } from '../actionRegistry';
import { APP_VIEWS } from '../../stores/navigationStore';
import {
  CAPACITES,
  POINTS_ENTREE,
  accesPrincipal,
  capacitesDeLaVue,
} from './manifeste';

describe('Le manifeste décrit chaque vue de l’application', () => {
  it('couvre toutes les vues déclarées, sans exception', () => {
    const vuesCouvertes = new Set(
      POINTS_ENTREE.filter((p) => p.binding.registre === 'vue').map((p) =>
        p.binding.registre === 'vue' ? p.binding.view : null,
      ),
    );

    const manquantes = APP_VIEWS.filter(
      (vue) => vue !== 'chat' && !vuesCouvertes.has(vue),
    );

    expect(manquantes).toEqual([]);
  });

  it('donne à chaque capacité un nom lisible par un non-technicien', () => {
    for (const capacite of CAPACITES) {
      expect(capacite.textes['fr-FR'].nom.length).toBeGreaterThan(2);
      // Un identifiant technique n'est pas un nom : ni point, ni tiret bas,
      // ni casse chameau. C'est ce qui distingue le manifeste d'un registre.
      expect(capacite.textes['fr-FR'].nom).not.toMatch(/[._]|[a-z][A-Z]/);
    }
  });

  it('dit à quoi sert chaque capacité, du point de vue de l’utilisateur', () => {
    for (const capacite of CAPACITES) {
      expect(capacite.textes['fr-FR'].quoi.length).toBeGreaterThan(15);
    }
  });
});

describe('Chaque chemin d’accès pointe vers du code qui existe', () => {
  it('ne référence aucune action inconnue du registre', () => {
    const actionsConnues = new Set(ACTIONS.map((a) => a.id));

    const orphelins = POINTS_ENTREE.filter(
      (p) =>
        (p.binding.registre === 'action' || p.binding.registre === 'raccourci') &&
        !actionsConnues.has(p.binding.actionId),
    ).map((p) => p.id);

    expect(orphelins).toEqual([]);
  });

  it('ne référence aucune vue inconnue', () => {
    const vuesConnues = new Set<string>(APP_VIEWS);

    const orphelins = POINTS_ENTREE.filter(
      (p) => p.binding.registre === 'vue' && !vuesConnues.has(p.binding.view),
    ).map((p) => p.id);

    expect(orphelins).toEqual([]);
  });

  it('ne référence aucune capacité inconnue', () => {
    const capacitesConnues = new Set(CAPACITES.map((c) => c.id));

    const orphelins = POINTS_ENTREE.flatMap((p) =>
      p.capacites.filter((id) => !capacitesConnues.has(id)).map(() => p.id),
    );

    expect(orphelins).toEqual([]);
  });

  it('relie chaque capacité à au moins un chemin réel', () => {
    const sansChemin = CAPACITES.filter((c) => c.entrees.length === 0).map((c) => c.id);

    expect(sansChemin).toEqual([]);
  });
});

describe('Les identifiants sont stables et sans ambiguïté', () => {
  it('n’a aucun identifiant de capacité en double', () => {
    const ids = CAPACITES.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('n’a aucun identifiant de point d’entrée en double', () => {
    const ids = POINTS_ENTREE.map((p) => p.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('n’a aucune collision de raccourci clavier', () => {
    const combinaisons = POINTS_ENTREE.filter(
      (p) => p.type === 'raccourci',
    ).map((p) => p.touches?.toLowerCase().replace(/\s+/g, ''));

    const definies = combinaisons.filter(Boolean);
    expect(new Set(definies).size).toBe(definies.length);
  });
});

describe('L’accès principal est déclaré, jamais déduit', () => {
  it('désigne exactement un accès principal par capacité', () => {
    for (const capacite of CAPACITES) {
      const principaux = POINTS_ENTREE.filter(
        (p) => capacite.entrees.includes(p.id) && p.principal,
      );

      expect(
        principaux.length,
        `la capacité « ${capacite.id} » n'a pas exactement un accès principal`,
      ).toBe(1);
    }
  });

  it('expose l’accès principal sans faire dépendre le résultat de l’ordre', () => {
    for (const capacite of CAPACITES) {
      expect(accesPrincipal(capacite.id)).toBeDefined();
    }
  });
});

describe('Mode fantôme : le manifeste dit la même chose que l’existant', () => {
  /**
   * Rien n'est encore branché. Ce test compare la sortie du manifeste à celle
   * des surfaces actuelles : tant qu'ils divergent, migrer un consommateur
   * changerait ce que voit l'utilisateur sans que personne ne l'ait décidé.
   */
  it('reprend les libellés de vue déjà affichés à l’écran', async () => {
    const { viewLabels } = await import(
      '../../components/prototype/PrototypeUnifiedViewCanvas'
    );

    for (const [vue, libelle] of Object.entries(viewLabels)) {
      const capacites = capacitesDeLaVue(vue as (typeof APP_VIEWS)[number]);

      expect(
        capacites.length,
        `aucune capacité ne décrit la vue « ${vue} »`,
      ).toBeGreaterThan(0);

      expect(
        capacites.map((c) => c.textes['fr-FR'].nom),
        `le manifeste renomme la vue « ${vue} » sans que ce soit décidé`,
      ).toContain(libelle);
    }
  });
});

describe('Le crosswalk est réel, pas déclaratif', () => {
  /**
   * Revue 0.44 : les gates vérifiaient que les identifiants EXISTENT, jamais
   * qu'ils pointent au BON endroit. En échangeant `email.open` et `crm.open`
   * dans le manifeste, tout restait vert — mais `/aide` aurait attribué les
   * mauvaises descriptions aux commandes.
   *
   * Ce test EXÉCUTE chaque action de navigation du manifeste et observe la vue
   * réellement ouverte. Une capacité qui déclare la vue `email` et l'action
   * `crm.open` échoue ici.
   */
  it('chaque action de navigation ouvre la vue que sa capacité déclare', async () => {
    const { runAction } = await import('../actionRegistry');
    const { useNavigationStore } = await import('../../stores/navigationStore');

    const setViewOriginal = useNavigationStore.getState().setView;
    const vuesOuvertes: string[] = [];
    useNavigationStore.setState({
      setView: (vue: (typeof APP_VIEWS)[number]) => {
        vuesOuvertes.push(vue);
      },
    });

    try {
      for (const capacite of CAPACITES) {
        const entrees = POINTS_ENTREE.filter((p) => capacite.entrees.includes(p.id));
        const vue = entrees.find((p) => p.binding.registre === 'vue');
        const action = entrees.find((p) => p.binding.registre === 'action');
        if (!vue || !action) continue;
        if (vue.binding.registre !== 'vue' || action.binding.registre !== 'action') continue;

        vuesOuvertes.length = 0;
        runAction(action.binding.actionId);

        expect(
          vuesOuvertes,
          `la capacité « ${capacite.id} » déclare la vue « ${vue.binding.view} » `
          + `mais son action « ${action.binding.actionId} » ouvre « ${vuesOuvertes[0] ?? 'rien'} »`,
        ).toContain(vue.binding.view);
      }
    } finally {
      useNavigationStore.setState({ setView: setViewOriginal });
    }
  });
});
