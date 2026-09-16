/**
 * P-061 (lot 0.74, persona Sophie c6) : « 1 variable résolue » alors que
 * {mauvais-nom} et {2eme sujet} partaient tels quels, sans un mot. Un jeton
 * qui ressemble à une variable sans en respecter la forme est signalé.
 */
import { describe, expect, it } from 'vitest';
import { jetonsMalFormes } from './variables';

describe('jetonsMalFormes', () => {
  it('relève les accolades dont le contenu n’est pas un nom de variable', () => {
    expect(jetonsMalFormes('Bonjour {prenom}, {mauvais-nom} et {2eme sujet}')).toEqual(['{mauvais-nom}', '{2eme sujet}']);
  });
  it('ignore les jetons valides, les accolades doublées et la syntaxe {action: …}', () => {
    expect(jetonsMalFormes('{nom_client} {{litteral}} {action: relance}')).toEqual([]);
  });
});
