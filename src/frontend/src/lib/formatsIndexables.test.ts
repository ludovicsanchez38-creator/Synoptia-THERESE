/**
 * L'interface et le serveur doivent parler des mêmes formats.
 *
 * Revue du 13/08/2026 : trois listes coexistaient sans source commune. Le
 * backend acceptait `.pptx`, `.xlsx`, `.cfg`, `.tex` ; l'explorateur ne les
 * proposait pas et offrait encore `.doc`, refusé côté serveur. Résultat :
 * l'utilisateur voyait un bouton d'indexation là où ça échouait, et pas de
 * bouton là où ça aurait marché.
 *
 * Ce test confronte la liste de l'interface au fichier Python qui fait
 * autorité. Aucune des deux ne peut plus bouger sans l'autre.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { EXTENSIONS_INDEXABLES, estIndexable, FILTRES_SELECTEUR } from './formatsIndexables';

const ici = dirname(fileURLToPath(import.meta.url));

/** Extensions déclarées par `path_security.INDEXABLE_EXTENSIONS`. */
function extensionsDuBackend(): Set<string> {
  const source = readFileSync(
    resolve(ici, '../../../backend/app/services/path_security.py'),
    'utf-8',
  );
  const bloc = source.match(/INDEXABLE_EXTENSIONS\s*=\s*\{([\s\S]*?)\n\}/);
  if (!bloc) throw new Error('bloc INDEXABLE_EXTENSIONS introuvable');

  // Les lignes de commentaire portent des extensions citées en prose
  // (« .xls, .ppt … étaient acceptés ») : elles ne déclarent rien.
  const sansCommentaires = bloc[1]
    .split('\n')
    .filter((l) => !l.trim().startsWith('#'))
    .join('\n');

  return new Set(sansCommentaires.match(/"(\.[a-z0-9]+)"/g)?.map((m) => m.slice(1, -1)) ?? []);
}

describe('les formats de l’interface suivent ceux du serveur', () => {
  const backend = extensionsDuBackend();

  it('le bloc du backend est bien lu', () => {
    expect(backend.size).toBeGreaterThan(40);
    expect(backend.has('.pdf')).toBe(true);
  });

  it("l'interface ne propose aucun format que le serveur refuse", () => {
    const enTrop = EXTENSIONS_INDEXABLES.filter((e) => !backend.has(e));

    expect(
      enTrop,
      `l'interface propose d'indexer ${enTrop.join(', ')}, que le serveur refuse : ` +
        `l'utilisateur clique et l'indexation échoue`,
    ).toEqual([]);
  });

  it("l'interface ne cache aucun format que le serveur accepte", () => {
    const oublies = [...backend].filter((e) => !EXTENSIONS_INDEXABLES.includes(e));

    expect(
      oublies,
      `le serveur sait lire ${oublies.join(', ')} mais l'interface ne le propose ` +
        `nulle part : la capacité existe et reste invisible`,
    ).toEqual([]);
  });

  it('reconnaît une extension avec ou sans point, en toutes casses', () => {
    expect(estIndexable('.PDF')).toBe(true);
    expect(estIndexable('pdf')).toBe(true);
    expect(estIndexable('.exe')).toBe(false);
    expect(estIndexable(undefined)).toBe(false);
    expect(estIndexable(null)).toBe(false);
  });

  it('ne propose aucun filtre Images dans le sélecteur', () => {
    // Aucune image n'est indexable : proposer le filtre menait à un échec dont
    // la cause n'était pas affichée.
    const noms = FILTRES_SELECTEUR.map((f) => f.name.toLowerCase());
    expect(noms.some((n) => n.includes('image'))).toBe(false);

    const toutes = FILTRES_SELECTEUR.flatMap((f) => f.extensions);
    for (const image of ['png', 'jpg', 'jpeg', 'gif', 'webp']) {
      expect(toutes, `le sélecteur propose ${image}, non indexable`).not.toContain(image);
    }
  });

  it('couvre les formats du sélecteur par la liste principale', () => {
    for (const filtre of FILTRES_SELECTEUR) {
      for (const extension of filtre.extensions) {
        expect(estIndexable(extension), `${extension} manque à la liste`).toBe(true);
      }
    }
  });
});
