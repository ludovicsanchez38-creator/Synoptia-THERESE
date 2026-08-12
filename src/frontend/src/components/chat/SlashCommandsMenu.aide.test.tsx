/**
 * L'aide doit être trouvable là où on la cherche.
 *
 * Inventaire des capacités du 13/08/2026 : la commande `/aide` existe côté
 * serveur — elle est même répondue localement, sans appel au modèle — mais elle
 * ne figurait pas dans le menu des commandes. Un utilisateur qui tape « / »
 * pour découvrir ce que THÉRÈSE sait faire ne pouvait donc pas trouver l'aide,
 * qui est exactement ce qu'il cherche à ce moment-là.
 */
import { describe, it, expect } from 'vitest';
import { SLASH_COMMANDS } from './SlashCommandsMenu';

describe("découvrabilité de l'aide", () => {
  it('propose /aide dans le menu des commandes', () => {
    const aide = SLASH_COMMANDS.find((c) => c.id === 'aide');

    expect(aide, "la commande /aide reste invisible de qui tape « / »").toBeDefined();
    expect(aide?.prefix).toBe('/aide');
  });

  it("décrit l'aide sans jargon", () => {
    const aide = SLASH_COMMANDS.find((c) => c.id === 'aide');

    // Un testeur doit comprendre ce qu'il obtient avant de cliquer.
    expect(aide?.description.toLowerCase()).toContain('sait faire');
  });

  it('ne déclare aucune commande en double', () => {
    const ids = SLASH_COMMANDS.map((c) => c.id);

    expect(new Set(ids).size, `identifiants dupliqués : ${ids}`).toBe(ids.length);
  });
});
