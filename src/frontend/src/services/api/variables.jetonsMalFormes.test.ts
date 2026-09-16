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
  it('audit release : du JSON, du code ou du CSS collés ne sont pas des variables ratées', () => {
    expect(jetonsMalFormes('Voici le JSON : {"a": 1, "b": "x"}')).toEqual([]);
    expect(jetonsMalFormes('function f() { return x; }')).toEqual([]);
    expect(jetonsMalFormes('.btn {margin: 0}')).toEqual([]);
  });
  it('audit release : un presque-nom avec majuscule ou tiret est signalé', () => {
    expect(jetonsMalFormes('Relance {Nom_Client} et {nom-client}')).toEqual(['{Nom_Client}', '{nom-client}']);
  });
});
