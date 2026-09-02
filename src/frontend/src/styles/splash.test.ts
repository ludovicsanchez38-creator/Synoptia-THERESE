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
