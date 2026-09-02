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

/* ------------------------------------------------------------------ B-152 */

/**
 * `qsa` échoue quand rien n'est trouvé ; `document.querySelector` rend `null`.
 * Les pas restés en appel brut transforment donc un sélecteur inventé en
 * verdict silencieux : « l'onboarding ne s'affiche pas » était vrai par
 * construction, quel que soit l'écran réel.
 *
 * Deux bornes tiennent cette garde à sa taille utile :
 *
 * 1. On ne juge qu'un groupe dont TOUS les sélecteurs citent un `data-testid`.
 *    Un repli `textarea`, `[role="alert"]` ou `.une-classe` peut trouver
 *    quelque chose : on ne sait pas le décider, on ne condamne pas.
 * 2. On saute les sections que les fichiers déclarent eux-mêmes piloter le
 *    SERVEUR (colonne « Produit » de l'index, ou titre de rubrique nommant
 *    Server) : ces identifiants appartiennent à une autre application.
 */
function texteCotéApplication(texte: string): string {
  const lignes = texte.split('\n');
  const scenariosServeur = new Set<string>();
  for (const ligne of lignes) {
    const rangee = /^\|\s*(\d+)\s*\|[^|]*\|\s*Server\s*\|/.exec(ligne);
    if (rangee) scenariosServeur.add(rangee[1]);
  }

  // Un scénario Server masque TOUTES ses rubriques ; une rubrique Server ne
  // masque qu'elle-même. Les deux mémoires sont donc distinctes.
  let scenarioMasque = false;
  let rubriqueMasquee = false;
  // Les blocs de code contiennent des commentaires shell qui commencent par
  // « # » : les prendre pour des titres démasquait la section suivante.
  let dansUnBlocDeCode = false;

  return lignes
    .map((ligne) => {
      if (/^\s*>?\s*```/.test(ligne)) dansUnBlocDeCode = !dansUnBlocDeCode;
      const titre = dansUnBlocDeCode ? null : /^(#{1,6})\s+(.*)$/.exec(ligne);
      if (titre) {
        const niveau = titre[1].length;
        if (niveau <= 2) {
          const scenario = /^Scenario\s+(\d+)\b/.exec(titre[2]);
          scenarioMasque = scenario ? scenariosServeur.has(scenario[1]) : false;
          rubriqueMasquee = false;
        } else {
          rubriqueMasquee = /\bServer\b/.test(titre[2]);
        }
      }
      // La ligne masquée est vidée, jamais supprimée : les numéros de ligne
      // rapportés doivent rester ceux du fichier.
      return scenarioMasque || rubriqueMasquee ? '' : ligne;
    })
    .join('\n');
}

/** Un groupe = des `document.querySelector(...)` enchaînés par `||`, c'est-à-dire
 *  « le premier qui trouve », la même sémantique que `qsa`. */
const GROUPE_BRUT =
  /(?:document\.querySelector(?:All)?\(\s*(?:['"`])(?:[\s\S]*?)(?:['"`])\s*\)\s*(?:\|\|\s*)?)+/g;
const SELECTEUR_BRUT = /document\.querySelector(?:All)?\(\s*(['"`])([\s\S]*?)\1\s*\)/g;

interface GroupeBrut {
  fichier: string;
  ligne: number;
  selecteurs: string[];
}

function groupesBruts(chemin: string, texte: string): GroupeBrut[] {
  const utile = texteCotéApplication(texte);
  const groupes: GroupeBrut[] = [];
  for (const groupe of utile.matchAll(GROUPE_BRUT)) {
    const selecteurs = [...groupe[0].matchAll(SELECTEUR_BRUT)].map((m) => m[2]);
    if (!selecteurs.length) continue;
    // Un seul repli non décidable suffit à sortir le groupe du périmètre.
    if (!selecteurs.every((s) => /\[data-testid=/.test(s))) continue;
    groupes.push({
      fichier: chemin,
      ligne: utile.slice(0, groupe.index).split('\n').length,
      selecteurs,
    });
  }
  return groupes;
}

const GROUPES_BRUTS = PROTOCOLES_APP.flatMap((chemin) =>
  groupesBruts(chemin.slice(RACINE.length + 1), readFileSync(chemin, 'utf-8')),
);

describe('B-152 : un verdict ne se décide pas par un sélecteur inventé', () => {
  it('la garde voit bien des appels bruts à analyser', () => {
    // Sans ce garde-fou, une expression régulière cassée rendrait zéro groupe
    // et le test suivant serait vert sans avoir rien lu.
    expect(GROUPES_BRUTS.length).toBeGreaterThan(0);
  });

  it('chaque groupe de data-testid a au moins un sélecteur présent dans le code', () => {
    const orphelins = GROUPES_BRUTS.filter(
      (groupe) => !groupe.selecteurs.some(selecteurExiste),
    ).map(
      (groupe) => `${groupe.fichier}:${groupe.ligne} → ${groupe.selecteurs.join(' | ')}`,
    );
    expect(
      orphelins,
      `ces pas rendent leur verdict sans rien mesurer :\n${orphelins.join('\n')}`,
    ).toEqual([]);
  });
});

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
