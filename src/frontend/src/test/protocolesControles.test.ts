/**
 * B-073 - un contrôle de protocole doit pouvoir échouer.
 *
 * Constat du 01/09/2026 (WP-086, reproduction RP06) : l'étape « XSS test » du
 * persona A3, marquée P0, vérifiait `window.__xss_triggered === undefined`.
 * Aucun code ne posait ce drapeau - ni la charge injectée
 * (`<img src=x onerror=alert(1)>` appelle `alert`, pas cette variable), ni
 * l'application, ni le protocole. La condition était donc vraie que l'injection
 * s'exécute ou non : le contrôle qui porte le nom du test ne pouvait pas
 * échouer.
 *
 * Ce gate ferme la porte à tout contrôle vide de la même famille : chaque
 * symbole global INTERROGÉ par un protocole doit être POSÉ quelque part, par le
 * protocole lui-même ou par l'application.
 *
 * Périmètre : les protocoles de l'application (`app/`) et leur socle commun
 * (`shared/`). Ceux du serveur (`server/`) relèvent d'une autre application et
 * ne sont pas dans ce lot ; S2-chef-service.md y lit un `window.__consoleErrors`
 * que rien ne pose, doublé il est vrai d'un relevé manuel - signalé, pas traité.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const racineDepot = join(__dirname, '..', '..', '..', '..');
const protocoles = join(racineDepot, 'tests', 'protocols');

function fichiersMarkdown(dossier: string): string[] {
  return readdirSync(dossier).flatMap((entree) => {
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) return fichiersMarkdown(chemin);
    return entree.endsWith('.md') ? [chemin] : [];
  });
}

describe('B-073 - tout symbole interrogé par un protocole est posé quelque part', () => {
  it('aucun contrôle ne repose sur un drapeau que rien ne pose', () => {
    const sources = [join(protocoles, 'app'), join(protocoles, 'shared')].flatMap(
      fichiersMarkdown,
    );
    expect(sources.length, 'aucun protocole lu').toBeGreaterThan(0);

    const corpus =
      sources.map((chemin) => readFileSync(chemin, 'utf-8')).join('\n') +
      '\n' +
      fichiersTypeScript(join(racineDepot, 'src', 'frontend', 'src'))
        .map((chemin) => readFileSync(chemin, 'utf-8'))
        .join('\n');

    const orphelins = new Set<string>();
    for (const chemin of sources) {
      const texte = readFileSync(chemin, 'utf-8');
      for (const trouve of texte.matchAll(/window\.(__[A-Za-z0-9_]+)/g)) {
        const symbole = trouve[1];
        // Une ÉCRITURE : `= ` et non `== `. Le cast TypeScript de
        // l'application (`(window as …).__therese = {`) est couvert : on
        // cherche le symbole, pas la forme `window.<symbole>`.
        const pose = new RegExp(`${symbole}\\s*=[^=]`);
        if (!pose.test(corpus)) orphelins.add(`${symbole} (${chemin.replace(racineDepot, '')})`);
      }
    }

    expect(
      [...orphelins],
      'symbole(s) interrogé(s) mais jamais posé(s) : le contrôle ne peut pas échouer',
    ).toEqual([]);
  });
});

function fichiersTypeScript(dossier: string): string[] {
  return readdirSync(dossier).flatMap((entree) => {
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) return fichiersTypeScript(chemin);
    return /\.tsx?$/.test(entree) && !/\.test\./.test(entree) ? [chemin] : [];
  });
}
