import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const CSS = readFileSync(join(__dirname, 'globals.css'), 'utf-8');

/** Bloc `@theme` : les valeurs du mode clair, celles que Tailwind compile. */
function blocTheme(): string {
  const debut = CSS.indexOf('@theme {');
  const fin = CSS.indexOf('\n}', debut);
  return CSS.slice(debut, fin);
}

function hex(valeur: string): [number, number, number] {
  const h = valeur.replace('#', '');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];
}

function luminance([r, g, b]: [number, number, number]): number {
  const f = (x: number) => {
    const v = x / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}

function contraste(a: [number, number, number], b: [number, number, number]): number {
  const [haut, bas] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (haut + 0.05) / (bas + 0.05);
}

/** `bg-agent-blue/20` : le jeton compose sur le blanc de la surface. */
function teinte(c: [number, number, number], alpha: number): [number, number, number] {
  return c.map((x) => Math.round(alpha * x + (1 - alpha) * 255)) as [number, number, number];
}

function jetonsDAgent(): Array<[string, [number, number, number]]> {
  const bloc = blocTheme();
  const trouves: Array<[string, [number, number, number]]> = [];
  // Elargi le 01/09/2026 aux jetons semantiques : warning tombait a 3,78:1
  // sur sa propre teinte a 20 %, et success a 4,11:1. Meme motif, meme cause.
  const motif = /--color-(agent-[\w-]+|warning|error|success|info):\s*(#[0-9A-Fa-f]{6})/g;
  for (const m of bloc.matchAll(motif)) {
    trouves.push([m[1], hex(m[2])]);
  }
  return trouves;
}

describe('contraste des couleurs d’agent sur leur propre teinte', () => {
  // Mesuré dans l'application lancée le 01/09/2026, instrument calibré : la
  // pastille « Moyenne » de l'écran des tâches ressortait à 4,33:1, répétée 74
  // fois. Le motif fautif est général : `text-agent-X` posé sur
  // `bg-agent-X/10` ou `/20`. Les six jetons avaient bien été assombris en
  // août — mais pour le fond de PAGE, jamais pour leur propre teinte, où ils
  // tombaient tous entre 3,81 et 4,30:1.
  it('chaque jeton reste lisible sur sa teinte à 10 % et à 20 %', () => {
    const fautifs: string[] = [];
    for (const [nom, couleur] of jetonsDAgent()) {
      // 30 % en plus des deux autres : la mesure dans l'application a montre
      // qu'une carte deja teintee rend le fond plus dense que le modele
      // « /20 sur du blanc », et que trois familles restaient a 4,21:1.
      for (const alpha of [0.1, 0.2, 0.3]) {
        const r = contraste(couleur, teinte(couleur, alpha));
        if (r < 4.5) fautifs.push(`${nom} sur sa teinte ${alpha * 100} % : ${r.toFixed(2)}:1`);
      }
    }
    expect(fautifs, fautifs.join(' | ')).toEqual([]);
  });

  it('le balayage porte bien sur les dix jetons, pas sur une liste vide', () => {
    expect(jetonsDAgent().length).toBe(10);
  });
});
