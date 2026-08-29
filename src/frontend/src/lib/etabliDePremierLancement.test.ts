/**
 * Sur une installation neuve, l'établi ne propose pas de facturer.
 *
 * Persona 08 (responsable administratif) : « Il y a écrit Interface unifiée et
 * Espace de travail. Je ne sais pas ce que c'est. En dessous, cinq boutons :
 * Écrire, Retrouver, Préparer, Facturer, Décider. Écrire, ça je comprends. Le
 * reste, je n'y touche pas. »
 *
 * Le médecin, l'écrivaine et la magistrate ont dit la même chose autrement :
 * l'accueil les habille en commerçant avant qu'ils aient rien demandé.
 */
import { describe, expect, it } from 'vitest';

import { ACTIONS_ETABLI } from './etabli';
import { actionsDeLEtabli } from './etabliDePremierLancement';

const ids = (actions: readonly { id: string }[]) => actions.map((a) => a.id);

describe("L'établi suit ce que l'installation contient", () => {
  it('une installation neuve ne propose pas Facturer', () => {
    const actions = actionsDeLEtabli({
      auMoinsUneFacture: false,
      infosSocieteCompletes: false,
    });
    expect(ids(actions)).not.toContain('invoice');
  });

  it('les quatre autres verbes restent, dans leur ordre', () => {
    const actions = actionsDeLEtabli({
      auMoinsUneFacture: false,
      infosSocieteCompletes: false,
    });
    expect(ids(actions)).toEqual(['email', 'memory', 'meeting', 'board']);
  });

  it('Facturer revient dès la première pièce', () => {
    const actions = actionsDeLEtabli({
      auMoinsUneFacture: true,
      infosSocieteCompletes: false,
    });
    expect(ids(actions)).toEqual(ids(ACTIONS_ETABLI));
  });

  it('Facturer revient aussi dès que les infos de société sont renseignées', () => {
    const actions = actionsDeLEtabli({
      auMoinsUneFacture: false,
      infosSocieteCompletes: true,
    });
    expect(ids(actions)).toEqual(ids(ACTIONS_ETABLI));
  });

  it('aucun autre verbe ne disparaît jamais', () => {
    for (const facture of [true, false]) {
      for (const societe of [true, false]) {
        const obtenus = ids(
          actionsDeLEtabli({ auMoinsUneFacture: facture, infosSocieteCompletes: societe }),
        );
        for (const attendu of ['email', 'memory', 'meeting', 'board']) {
          expect(obtenus).toContain(attendu);
        }
      }
    }
  });
});
