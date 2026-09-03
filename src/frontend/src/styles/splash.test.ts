/**
 * B-063 - l'écran de démarrage porte les couleurs de la charte.
 *
 * Constat du 01/09/2026 (cartographie WP-056) : `index.html` codait en dur
 * #0f0f13, #00d4ff et #ff00aa, quand la charte dit #0B1226, #22D3EE et
 * #E11D8D. La teinte #0f0f13 n'existait nulle part ailleurs dans le dépôt : au
 * montage de React, le fond sautait d'un presque-noir à un bleu nuit. Son
 * propre commentaire annonçait pourtant « variables alignées sur le thème ».
 *
 * Le splash s'affiche AVANT le bundle : il ne peut pas lire globals.css et doit
 * donc recopier ses valeurs. Ces tests lisent les deux fichiers et refusent que
 * les copies divergent - l'audit graphique des 0.60 et 0.61 avait balayé
 * l'application React, jamais cette page d'amorçage.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const racineFront = join(__dirname, '..', '..');
const lire = (chemin: string) => readFileSync(join(racineFront, chemin), 'utf-8');

const indexHtml = lire('index.html');
const globals = lire('src/styles/globals.css');

/** Valeur d'une variable CSS dans un bloc délimité par son sélecteur. */
function variable(css: string, selecteur: string, nom: string): string {
  const debut = css.indexOf(selecteur);
  expect(debut, `bloc ${selecteur} introuvable`).toBeGreaterThanOrEqual(0);
  const bloc = css.slice(debut, css.indexOf('\n}', debut));
  const trouve = new RegExp(`${nom}:\\s*([^;]+);`).exec(bloc);
  expect(trouve, `${nom} introuvable dans ${selecteur}`).not.toBeNull();
  return (trouve as RegExpExecArray)[1].trim().toLowerCase();
}

describe('B-063 - l’écran de démarrage est aux couleurs de la charte', () => {
  it('aucune teinte du splash n’est inventée : toutes viennent de globals.css', () => {
    const teintes = [...indexHtml.matchAll(/#[0-9a-fA-F]{6}\b/g)].map((m) => m[0].toLowerCase());
    expect(teintes.length, 'aucune couleur lue dans index.html').toBeGreaterThan(0);

    const charte = globals.toLowerCase();
    const orphelines = teintes.filter((teinte) => !charte.includes(teinte));
    expect(
      orphelines,
      `teinte(s) absente(s) de globals.css : ${orphelines.join(', ')}`,
    ).toEqual([]);
  });

  it('le fond du splash est celui du thème sombre, et les accents ceux de la marque', () => {
    expect(variable(indexHtml, ':root {', '--therese-bg')).toBe(
      variable(globals, '[data-theme="dark"] {', '--color-bg'),
    );
    expect(variable(indexHtml, ':root {', '--therese-cyan')).toBe(
      variable(globals, '@theme {', '--color-accent-cyan'),
    );
    expect(variable(indexHtml, ':root {', '--therese-magenta')).toBe(
      variable(globals, '@theme {', '--color-accent-magenta'),
    );
  });
});

/**
 * B-065 — le splash d'amorçage animait en boucle malgré `prefers-reduced-motion`.
 *
 * Mesure du 01/09/2026 (Playwright, `emulateMedia({reducedMotion:'reduce'})`,
 * lecture immédiate) : `animation-iteration-count` valait `infinite` pour
 * `therese-pulse` (titre) et `therese-spin` (roue), alors que le splash React
 * coupe déjà l'animation dans ce cas (SplashScreen.tsx:243). Au moment mesuré,
 * `document.styleSheets.length` valait 1 : seule la feuille inline s'applique,
 * `globals.css` et sa règle universelle ne sont pas encore là. Le garde devait
 * donc vivre dans le `<style>` de la page, pas ailleurs.
 *
 * Le test porte aussi sur la POSITION du bloc : à spécificité égale, c'est la
 * dernière déclaration qui l'emporte. Un `@media` écrit au-dessus des règles
 * animées passerait un test de contenu naïf sans rien neutraliser.
 */
describe('B-065 — le splash respecte le mouvement réduit', () => {
  const style = (() => {
    const debut = indexHtml.indexOf('<style>');
    const fin = indexHtml.indexOf('</style>', debut);
    expect(debut, '<style> inline introuvable dans index.html').toBeGreaterThanOrEqual(0);
    expect(fin, '</style> introuvable dans index.html').toBeGreaterThan(debut);
    return indexHtml.slice(debut, fin);
  })();

  it('le style inline porte un bloc prefers-reduced-motion', () => {
    expect(/@media\s*\(prefers-reduced-motion:\s*reduce\)/.test(style)).toBe(true);
  });

  it('le bloc neutralise les deux animations en boucle du splash', () => {
    const debut = style.search(/@media\s*\(prefers-reduced-motion:\s*reduce\)/);
    const bloc = style.slice(debut);
    for (const selecteur of ['#therese-splash h1', '#therese-splash .therese-spinner']) {
      const position = bloc.indexOf(selecteur);
      expect(position, `${selecteur} absent du bloc mouvement réduit`).toBeGreaterThanOrEqual(0);
      const regle = bloc.slice(position, bloc.indexOf('}', position));
      expect(/animation:\s*none/.test(regle), `${selecteur} n’annule pas son animation`).toBe(true);
    }
  });

  it('le bloc est écrit APRÈS les règles animées, sinon la cascade l’ignore', () => {
    const garde = style.search(/@media\s*\(prefers-reduced-motion:\s*reduce\)/);
    for (const animation of ['therese-pulse', 'therese-spin']) {
      const declaration = style.indexOf(`animation: ${animation}`);
      expect(declaration, `animation ${animation} introuvable`).toBeGreaterThanOrEqual(0);
      expect(
        garde,
        `le garde de mouvement réduit précède « animation: ${animation} » : la cascade le neutralise`,
      ).toBeGreaterThan(declaration);
    }
  });
});

/**
 * B-297 - le splash et l'application ne décrivaient pas la même fenêtre.
 *
 * `tauri.conf.json` déclare la fenêtre `transparent: true` et
 * `decorations: false` : sa forme ne vient que du CSS. La feuille globale rend
 * `html` transparent et arrondit `body` et `#root` de `--radius-md` ; le splash
 * inline, lui, peignait `html` ET `body` d'une couleur opaque, à angles vifs.
 * Au montage de React la fenêtre changeait donc de FORME en même temps que de
 * couleur. Le test des teintes (B-063) ne verrouillait que les couleurs.
 *
 * Le rayon doit être posé sur `#therese-splash` lui-même : il est en
 * `position: fixed`, donc l'`overflow: hidden` de `body` ne le rogne pas.
 */
describe('B-297 - le splash a la même forme que la fenêtre de l’application', () => {
  const style = (() => {
    const debut = indexHtml.indexOf('<style>');
    return indexHtml.slice(debut, indexHtml.indexOf('</style>', debut));
  })();

  /** Corps de la règle CSS d'un sélecteur, dans le <style> inline. */
  function regle(selecteur: string): string {
    const ancre = new RegExp(`(^|\\n)\\s*${selecteur.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\{`);
    const trouve = ancre.exec(style);
    expect(trouve, `règle « ${selecteur} » introuvable dans le <style> d’index.html`).not.toBeNull();
    const debut = style.indexOf('{', (trouve as RegExpExecArray).index);
    return style.slice(debut, style.indexOf('}', debut));
  }

  it('le rayon du splash n’est pas inventé : c’est --radius-md de la charte', () => {
    expect(variable(indexHtml, ':root {', '--therese-radius')).toBe(
      variable(globals, '@theme {', '--radius-md'),
    );
  });

  it('html est transparent, comme dans la feuille globale', () => {
    expect(regle('html')).toMatch(/background:\s*transparent\s*;/);
  });

  it('body porte le fond et le rayon, comme dans la feuille globale', () => {
    const corps = regle('body');
    expect(corps).toMatch(/background:\s*var\(--therese-bg\)\s*;/);
    expect(corps).toMatch(/border-radius:\s*var\(--therese-radius\)\s*;/);
  });

  it('le calque du splash est arrondi lui aussi (il est en position fixed)', () => {
    expect(regle('#therese-splash')).toMatch(/border-radius:\s*var\(--therese-radius\)\s*;/);
  });
});
