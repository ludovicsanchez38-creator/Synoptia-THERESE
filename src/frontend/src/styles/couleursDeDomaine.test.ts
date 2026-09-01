/**
 * Lot 5 du plan de cohérence graphique (30/08/2026) : plus de couleur brute.
 *
 * 165 couleurs Tailwind brutes servaient de couleur de texte, toutes entre
 * 1,54:1 et 2,44:1 sur le fond clair : des nuances -400 pensées pour un fond
 * sombre, jamais redéclinées quand le thème clair est devenu le défaut. Le
 * correctif de BUG-150 avait fait ce travail pour l'Atelier seulement.
 *
 * Correction due à l'audit : celui-ci annonçait « 102 text-red-400 ». Il y en
 * avait deux dans tout le dépôt. Le vrai volume était ailleurs, en vert, en
 * violet et en cyan.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = resolve(process.cwd(), 'src');
const CSS = readFileSync(join(RACINE, 'styles/globals.css'), 'utf-8');

const SOURCES: string[] = [];
(function collecter(dossier: string) {
  for (const e of readdirSync(dossier, { withFileTypes: true })) {
    const chemin = join(dossier, e.name);
    if (e.isDirectory()) collecter(chemin);
    else if (/\.tsx$/.test(e.name) && !/\.test\.tsx$/.test(e.name)) SOURCES.push(chemin);
  }
})(RACINE);

const court = (f: string) => f.slice(f.lastIndexOf('/src/') + 5);

function luminance(hex: string): number {
  const v = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = parseInt(v.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contraste(a: string, b: string): number {
  const [h, l] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (h + 0.05) / (l + 0.05);
}
function bloc(marqueur: string): Record<string, string> {
  // Ancré en début de ligne : cf. le même défaut corrigé dans a11y.test.tsx.
  const ancre = new RegExp(`^${marqueur.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\{`, 'm');
  const trouve = ancre.exec(CSS);
  const debut = trouve ? trouve.index : -1;
  const ouvre = CSS.indexOf('{', debut);
  let profondeur = 0;
  let fin = ouvre;
  for (let i = ouvre; i < CSS.length; i++) {
    if (CSS[i] === '{') profondeur++;
    else if (CSS[i] === '}' && --profondeur === 0) {
      fin = i;
      break;
    }
  }
  const out: Record<string, string> = {};
  for (const m of CSS.slice(ouvre, fin).matchAll(/--color-([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;/g)) {
    out[m[1]] = m[2];
  }
  return out;
}

const CLAIR = bloc('@theme');
const SOMBRE = { ...CLAIR, ...bloc('[data-theme="dark"]') };

// Tous les remplissages sur lesquels on pose du texte. En clair ils sont
// sombres, en sombre ils sont clairs : l'encre doit donc suivre le thème.
const REMPLISSAGES = [
  'accent', 'success', 'warning', 'error', 'info',
  'agent-cyan', 'agent-blue', 'agent-green', 'agent-purple', 'agent-amber', 'agent-magenta',
  'domaine-agenda', 'domaine-taches', 'domaine-factures', 'domaine-prospects',
] as const;
const DOMAINES = ['agenda', 'taches', 'factures', 'prospects'] as const;

describe('lot 5 : plus une seule couleur brute', () => {
  it("aucune couleur Tailwind brute, ni en texte ni en fond", () => {
    // La première version ne regardait que le texte : 206 fonds, bordures et
    // anneaux bruts sont restés, tous en nuances 400/500/600 pensées pour un
    // fond sombre. Un survol qui passe de green-500/20 à /30 faisait tomber
    // une action sous le seuil, et rien ne le voyait.
    const familles =
      'red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose';
    const motif = new RegExp(
      `\\b(?:text|bg|border|ring|from|to|via|placeholder|divide|outline|shadow|decoration|accent|caret)-(?:${familles})-\\d{2,3}\\b`,
      'g',
    );
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(motif)) fautifs.push(`${court(f)} : ${m[0]}`);
    }
    expect(fautifs, `${fautifs.length} couleurs, ex. ${fautifs.slice(0, 3).join(' | ')}`).toEqual([]);
  });

  it.each(DOMAINES)('le domaine %s est lisible sur sa propre teinte, dans les deux thèmes', (nom) => {
    for (const [theme, jetons] of [['clair', CLAIR], ['sombre', SOMBRE]] as const) {
      const encre = jetons[`domaine-${nom}`];
      const teinte = jetons[`domaine-${nom}-tint`];
      expect(encre, `--color-domaine-${nom} absent du thème ${theme}`).toBeTruthy();
      expect(teinte, `--color-domaine-${nom}-tint absent du thème ${theme}`).toBeTruthy();
      expect(contraste(encre, teinte), `${nom} sur sa teinte (${theme})`).toBeGreaterThanOrEqual(4.5);
      expect(contraste(encre, jetons['bg']), `${nom} sur le fond (${theme})`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it('les couleurs de domaine sont réellement portées par une surface', () => {
    // Un jeton défini que personne n'utilise, c'est la maladie qu'on soigne.
    const porteurs = SOURCES.filter((f) => /domaine-(agenda|taches|factures|prospects)/.test(readFileSync(f, 'utf-8')));
    expect(porteurs.length, 'aucun composant ne porte les couleurs de domaine').toBeGreaterThanOrEqual(1);
  });
  it.each(['clair', 'sombre'])("l'encre sur remplissage passe AA en thème %s", (theme) => {
    // Trouvé par la revue adverse le 30/08/2026 : je n'avais mesuré que le
    // thème clair. En sombre, les mêmes jetons sont des couleurs CLAIRES, et
    // le blanc y tombe entre 1,67:1 et 3,31:1 sur chacun d'eux.
    const jetons = theme === 'clair' ? CLAIR : SOMBRE;
    const encre = jetons['ink-on-fill'];
    expect(encre, `--color-ink-on-fill absent du thème ${theme}`).toBeTruthy();
    for (const nom of REMPLISSAGES) {
      const fond = jetons[nom];
      if (!fond) continue;
      expect(contraste(encre, fond), `ink-on-fill sur ${nom} (${theme})`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("aucune encre figée dans les composants", () => {
    // Interdiction ferme, pas une detection a la ligne. La revue adverse du
    // 30/08/2026 a montre qu'une regle « text-white sur la meme ligne qu'un
    // bg-* » ne voit rien : dans PipelineView le fond vient d'une constante,
    // dans BoardPanel d'un tableau de classes multiligne, et une icone blanche
    // vit dans un enfant du bloc colore. Onze defauts avaient survecu.
    //
    // text-white, text-bg et text-background sont des valeurs de theme figees.
    // Sur un remplissage d'accent, de domaine ou d'agent, l'une des deux
    // versions du theme est forcement illisible : en clair ces remplissages
    // sont sombres, en sombre ils sont clairs. C'est --color-ink-on-fill qui
    // repond, ou text-accent-ink sur le cyan, constant dans les deux themes.
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      readFileSync(f, 'utf-8')
        .split('\n')
        .forEach((ligne, i) => {
          if (/\btext-(white|bg|background)\b/.test(ligne)) fautifs.push(`${court(f)}:${i + 1}`);
        });
    }
    expect(fautifs, `${fautifs.length} encres figées : ${fautifs.slice(0, 5).join(', ')}`).toEqual([]);
  });

  it("les couleurs de domaine ne sont pas nommées par un numéro", () => {
    // --k1..--k4 venaient de la maquette de mai. Ils portaient les mêmes
    // quatre couleurs, avec le même défaut de contraste, sous des noms que
    // personne ne peut lire. Un seul jeu, nommé par le domaine.
    const fautifs: string[] = [];
    for (const f of [...SOURCES, join(RACINE, 'styles/globals.css')]) {
      const contenu = readFileSync(f, 'utf-8');
      // Le motif litteral ne rencontrait jamais `--k${(i % 4) + 1}`, assemble
      // a l'execution : le test restait vert en nommant un defaut vivant dans
      // deux fichiers de son propre perimetre. Il voit desormais les deux formes.
      for (const m of contenu.matchAll(/--k(?:[1-4]|\$\{)[\w\s%()+*-]*(bg)?/g)) {
        if (/^\s*\/[/*]|^\s*\*/.test(contenu.slice(contenu.lastIndexOf('\n', m.index) + 1, m.index))) continue;
        fautifs.push(`${court(f)} : ${m[0]}`);
      }
    }
    expect(fautifs, fautifs.slice(0, 4).join(' | ')).toEqual([]);
  });

  it("les seules couleurs en dur sont celles qui doivent l'être", () => {
    // Une couleur écrite en hexadécimal dans un className échappe au thème :
    // elle est identique en clair et en sombre. Deux familles le justifient,
    // et seulement deux.
    const LEGITIMES = new Set([
      // Blocs de code : un terminal reste sombre dans les deux thèmes.
      '#0A0F1E', '#0a0f1e', '#131B35', '#1e1e1e', '#B6C7DA',
      // Boutons de fenêtre macOS : ces trois valeurs sont imposées par le système.
      '#FF5F57', '#FEBC2E', '#28C840',
    ]);
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(
        /\b(?:bg|text|border|ring|from|to|via)-\[(#[0-9A-Fa-f]{3,8})\]/g,
      )) {
        if (!LEGITIMES.has(m[1])) fautifs.push(`${court(f)} : ${m[0]}`);
      }
    }
    expect(fautifs, fautifs.slice(0, 4).join(' | ')).toEqual([]);
  });

  it("aucune couleur de thème n'est posée en style inline", () => {
    // Le trou que le balayage de l'application lancée a révélé le 30/08/2026 :
    // les cinq conseillers du Board portaient leur couleur en style inline,
    // depuis un objet JS. Aucune règle sur les className ne pouvait la voir.
    // Mesurée à 1,81:1 sur fond blanc, sur quatre écrans.
    //
    // Restent autorisées les couleurs qui ne sont PAS des couleurs de thème :
    // l'identité des fournisseurs de modèles (mêlée à l'encre du thème au
    // rendu) et la table de référence du thème sombre.
    const EXCEPTIONS = new Set([
      'components/board/AdvisorCard.tsx', // marques Claude, GPT, Gemini, Mistral, Grok, Ollama
      'lib/accessibility.ts', // table de référence, pas du rendu
    ]);
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      const chemin = court(f);
      if ([...EXCEPTIONS].some((e) => chemin.endsWith(e))) continue;
      for (const m of readFileSync(f, 'utf-8').matchAll(
        /\b(color|backgroundColor|background|borderColor|fill|stroke)\s*:\s*['"`]#[0-9A-Fa-f]{3,8}['"`]/g,
      )) {
        fautifs.push(`${chemin} : ${m[0].slice(0, 40)}`);
      }
    }
    expect(fautifs, `${fautifs.length} couleurs inline : ${fautifs.slice(0, 4).join(' | ')}`).toEqual([]);
  });

  it("la charte Synoptïa ne déborde pas sur THÉRÈSE", () => {
    // Arbitrage de Ludo, 30/08/2026 : THÉRÈSE porte son identité propre.
    // #2451FF est le bleu de la marque Synoptïa.
    const fautifs = SOURCES.filter((f) => /2451FF/i.test(readFileSync(f, 'utf-8')));
    expect(fautifs.map(court)).toEqual([]);
  });
});
