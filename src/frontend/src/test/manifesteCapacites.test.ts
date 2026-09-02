/**
 * B-143 : la description du manifeste Tauri annonçait un périmètre qu'elle
 * n'avait pas.
 *
 * « filesystem scoped to $HOME/.therese and $APPDATA » face à CINQ permissions
 * de lecture accordées sur `$HOME/**` — lire, lire du texte, exister, lister un
 * dossier, statuer — et à des écritures qui touchent aussi `$DOWNLOAD`. Toute
 * la maison de l'utilisateur est lisible ; c'est la phrase qui mentait, pas les
 * permissions : `FileBrowser` explore réellement le dossier personnel
 * (`homeDir()` / `readDir()` / `stat()`), les resserrer casserait l'explorateur.
 *
 * La garde verrouille les DEUX sens. Élargir une permission sans corriger la
 * phrase échoue ; promettre dans la phrase un chemin qu'on n'accorde pas
 * échoue aussi. Elle refuse également une permission `fs:` d'un genre inconnu :
 * une nouvelle capacité doit être classée par un humain, pas absorbée.
 */
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// vitest tourne depuis src/frontend.
const MANIFESTE = resolve(process.cwd(), 'src-tauri/capabilities/default.json');

interface PermissionDetaillee {
  identifier: string;
  allow?: { path?: string }[];
  deny?: { path?: string }[];
}

const manifeste = JSON.parse(readFileSync(MANIFESTE, 'utf-8')) as {
  description: string;
  permissions: (string | PermissionDetaillee)[];
};

/** La racine d'un motif : ce qui précède le premier joker. `$HOME/**` → `$HOME`,
 *  `$HOME/.therese/**` → `$HOME/.therese`, `$HOME` → `$HOME`. */
function racine(motif: string): string {
  const segments = motif.split('/');
  const utiles: string[] = [];
  for (const segment of segments) {
    if (segment.includes('*')) break;
    utiles.push(segment);
  }
  return utiles.join('/');
}

const LECTURE = /read|exists|stat/;
const ECRITURE = /write|mkdir|remove|rename|copy/;

const accordees = { lecture: new Set<string>(), ecriture: new Set<string>() };
const refusees = new Set<string>();
const nonClassees: string[] = [];

for (const permission of manifeste.permissions) {
  if (typeof permission === 'string') continue;
  const { identifier, allow = [], deny = [] } = permission;
  if (!identifier.startsWith('fs:')) continue;

  for (const entree of deny) {
    if (entree.path) refusees.add(racine(entree.path));
  }
  if (!allow.length) continue;

  const genre = LECTURE.test(identifier)
    ? 'lecture'
    : ECRITURE.test(identifier)
      ? 'ecriture'
      : null;
  if (!genre) {
    nonClassees.push(identifier);
    continue;
  }
  for (const entree of allow) {
    if (entree.path) accordees[genre].add(racine(entree.path));
  }
}

/** Les chemins que la phrase revendique, rubrique par rubrique. La description
 *  est écrite en segments étiquetés justement pour être vérifiable. */
function chemainsDeclares(rubrique: string): Set<string> {
  const segment = manifeste.description
    .split('|')
    .map((morceau) => morceau.trim())
    .find((morceau) => morceau.toLowerCase().includes(rubrique));
  if (!segment) return new Set();
  return new Set(segment.match(/\$[A-Z]+(?:\/[A-Za-z0-9_.-]+)*/g) ?? []);
}

const trie = (ensemble: Set<string>) => [...ensemble].sort();

describe('B-143 : la description du manifeste dit le périmètre réellement accordé', () => {
  it('toute permission fs: est d’un genre connu', () => {
    expect(
      nonClassees,
      `permissions fs: ni lecture ni écriture, à classer : ${nonClassees.join(', ')}`,
    ).toEqual([]);
  });

  it('la garde a bien lu des permissions à vérifier', () => {
    // Un manifeste mal parcouru rendrait des ensembles vides, et l'égalité
    // « rien accordé = rien déclaré » serait vraie sans rien prouver.
    expect(accordees.lecture.size).toBeGreaterThan(0);
    expect(accordees.ecriture.size).toBeGreaterThan(0);
    expect(refusees.size).toBeGreaterThan(0);
  });

  it('la phrase nomme exactement les racines accordées en lecture', () => {
    expect(trie(chemainsDeclares('read:'))).toEqual(trie(accordees.lecture));
  });

  it('la phrase nomme exactement les racines accordées en écriture', () => {
    expect(trie(chemainsDeclares('write:'))).toEqual(trie(accordees.ecriture));
  });

  it('la phrase nomme exactement les chemins refusés', () => {
    expect(trie(chemainsDeclares('denied:'))).toEqual(trie(refusees));
  });
});
