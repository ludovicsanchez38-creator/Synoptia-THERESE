/**
 * Le repli hors ligne des Réglages doit ouvrir chaque fournisseur sur la
 * même tête que le catalogue du moteur. Un alias (-latest) n'est pas une
 * tête : il peut désigner un autre modèle au prochain relevé.
 *
 * Ollama n'a pas de liste statique : ses modèles viennent de la machine.
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import { FOURNISSEURS } from './catalogueModeles';

const ici = dirname(fileURLToPath(import.meta.url));

/** Première entrée de `modeles=(...)` pour chaque fiche de `CATALOGUE` */
function tetesDuCatalogue(source: string): Map<string, string> {
  const debut = source.indexOf('CATALOGUE:');
  if (debut < 0) throw new Error('CATALOGUE introuvable');
  const corps = source.slice(debut);
  const tetes = new Map<string, string>();
  for (const match of corps.matchAll(/"([a-z0-9]+)":\s*FicheFournisseur\(/g)) {
    const nom = match[1];
    const apres = corps.slice((match.index ?? 0) + match[0].length);
    const modeles = apres.match(/modeles=\(/);
    if (!modeles || modeles.index === undefined) {
      throw new Error(`modeles introuvable pour ${nom}`);
    }
    const suite = apres.slice(modeles.index + 'modeles=('.length);
    let tete: string | undefined;
    for (const ligne of suite.split('\n')) {
      const code = ligne.split('#')[0] ?? '';
      const id = code.match(/"([^"]+)"/);
      if (id) {
        tete = id[1];
        break;
      }
    }
    if (!tete) throw new Error(`tête introuvable pour ${nom}`);
    tetes.set(nom, tete);
  }
  return tetes;
}

describe('le repli a la même tête que le catalogue', () => {
  const source = readFileSync(
    resolve(ici, '../../../backend/app/services/modeles_catalogue.py'),
    'utf-8',
  );
  const catalogue = tetesDuCatalogue(source);

  it('compare la tête de chaque fournisseur du repli à celle du catalogue', () => {
    expect(catalogue.get('mistral')).toBe('mistral-medium-3-5');
    expect(catalogue.get('anthropic')).toBe('claude-opus-5-5');
    expect(FOURNISSEURS.filter((f) => f.models.length === 0).map((f) => f.id)).toEqual(['ollama']);

    const ecarts = FOURNISSEURS.flatMap((fournisseur) => {
      const tete = fournisseur.models[0]?.id;
      if (!tete) return [];
      const attendue = catalogue.get(fournisseur.id);
      if (attendue === undefined) return [`${fournisseur.id} absent du catalogue`];
      if (tete !== attendue) return [`${fournisseur.id} : repli ${tete}, catalogue ${attendue}`];
      return [];
    });
    const mistral = FOURNISSEURS.find((f) => f.id === 'mistral');
    const medium35 = (mistral?.models ?? [])
      .filter((m) => m.name === 'Mistral Medium 3.5')
      .map((m) => m.id);

    expect({ ecarts, medium35 }).toEqual({
      ecarts: [],
      medium35: ['mistral-medium-3-5'],
    });
  });
});
