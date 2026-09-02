/**
 * B-151 : les sélecteurs confiés à `qsa` doivent désigner des éléments réels.
 *
 * `qsa` (défini en tête des protocoles) parcourt ses sélecteurs et JETTE quand
 * aucun ne trouve rien. Un sélecteur inventé n'est donc pas une mesure à zéro :
 * il interrompt le scénario. Les verdicts « données préservées », « pas de
 * doublon de facture » et « contacts/tâches restants » étaient inatteignables.
 *
 * Cette garde relit les protocoles et exige, pour CHAQUE appel `qsa`, qu'au
 * moins un de ses sélecteurs existe dans le code de l'interface — exactement la
 * sémantique de `qsa`, qui se contente du premier sélecteur qui trouve.
 *
 * Périmètre : les protocoles qui pilotent CETTE application (app/ et shared/).
 * `tests/protocols/server/` pilote une autre application (Synoptia-THERESE-Server,
 * dépôt distinct) : ses sélecteurs n'ont aucune raison d'exister ici.
 */
import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { relative, resolve, sep } from 'node:path';

// vitest tourne depuis src/frontend ; les protocoles sont à la racine du dépôt.
const RACINE = resolve(process.cwd(), '../..');
const PROTOCOLES = resolve(RACINE, 'tests/protocols');
const SOURCES = resolve(process.cwd(), 'src');

function fichiers(racine: string, garde: (nom: string) => boolean): string[] {
  const trouves: string[] = [];
  const parcourir = (dossier: string) => {
    for (const entree of readdirSync(dossier)) {
      if (entree === 'node_modules' || entree.startsWith('.')) continue;
      const chemin = resolve(dossier, entree);
      if (statSync(chemin).isDirectory()) parcourir(chemin);
      else if (garde(entree)) trouves.push(chemin);
    }
  };
  parcourir(racine);
  return trouves;
}

/** Le code de l'interface, sans les fichiers de test : un sélecteur qui
 *  n'existe que dans un test ne prouve rien à l'écran. */
const CODE_INTERFACE = fichiers(
  SOURCES,
  (nom) => /\.(ts|tsx)$/.test(nom) && !/\.(test|spec)\.(ts|tsx)$/.test(nom),
)
  .map((f) => readFileSync(f, 'utf-8'))
  .join('\n');

interface AppelQsa {
  fichier: string;
  ligne: number;
  selecteurs: string[];
}

function appelsQsa(chemin: string, texte: string): AppelQsa[] {
  const lignes = texte.split('\n');
  const appels: AppelQsa[] = [];
  lignes.forEach((ligne, index) => {
    // La DÉFINITION de l'aide (`function qsa(...selecteurs)`) n'est pas un appel.
    if (/function\s+qsa\s*\(/.test(ligne)) return;
    const appel = /\bqsa\(([^)]*)\)/.exec(ligne);
    if (!appel) return;
    const selecteurs = [...appel[1].matchAll(/'([^']+)'|"([^"]+)"/g)].map(
      (m) => m[1] ?? m[2],
    );
    if (selecteurs.length) {
      appels.push({ fichier: chemin, ligne: index + 1, selecteurs });
    }
  });
  return appels;
}

/** Un sélecteur existe si son identifiant apparaît TEL QUEL dans le code.
 *  L'égalité est exacte à dessein : `sidebar-conversation-item` ne satisfait
 *  pas `[data-testid="conversation-item"]`, il désigne autre chose. */
function selecteurExiste(selecteur: string): boolean {
  const testid = /\[data-testid=["']?([^"'\]]+)["']?\]/.exec(selecteur);
  if (testid) {
    const nom = testid[1].replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`["'\`]${nom}["'\`]`).test(CODE_INTERFACE);
  }
  const classe = /^\.([A-Za-z0-9_-]+)$/.exec(selecteur);
  if (classe) {
    const nom = classe[1].replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`(^|[\\s"'\`])${nom}([\\s"'\`]|$)`, 'm').test(CODE_INTERFACE);
  }
  // Sélecteur d'une autre forme (attribut, rôle) : on ne sait pas le décider,
  // on ne le compte donc pas comme une preuve d'existence.
  return false;
}

const PROTOCOLES_APP = fichiers(PROTOCOLES, (nom) => nom.endsWith('.md')).filter(
  (chemin) => relative(PROTOCOLES, chemin).split(sep)[0] !== 'server',
);

const APPELS = PROTOCOLES_APP.flatMap((chemin) =>
  appelsQsa(chemin.slice(RACINE.length + 1), readFileSync(chemin, 'utf-8')),
);

describe('B-151 : les sélecteurs des protocoles désignent des éléments réels', () => {
  it('les protocoles de cette application contiennent bien des appels qsa', () => {
    expect(APPELS.length).toBeGreaterThan(0);
  });

  it('chaque appel qsa a au moins un sélecteur présent dans le code', () => {
    const orphelins = APPELS.filter(
      (appel) => !appel.selecteurs.some(selecteurExiste),
    ).map(
      (appel) => `${appel.fichier}:${appel.ligne} → ${appel.selecteurs.join(' | ')}`,
    );
    expect(orphelins, `qsa jetterait sur ces appels :\n${orphelins.join('\n')}`).toEqual([]);
  });
});
