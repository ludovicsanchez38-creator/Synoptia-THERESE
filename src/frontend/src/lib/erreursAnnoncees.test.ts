/**
 * Un échec silencieux n'existe que pour l'œil.
 *
 * Le socle P3 du plan visait « chargement, erreur, état vide ». Le bandeau
 * d'erreur qui s'affiche après une action - sauvegarde refusée, suppression
 * impossible - apparaît dans le DOM sans rien annoncer : un lecteur d'écran
 * ne le lit pas, et la personne croit son enregistrement passé.
 *
 * La règle porte sur le bandeau conditionné à un état d'erreur (`{error && …}`)
 * dans les formulaires où l'on agit. Les variantes de style (un bouton rouge)
 * ne sont pas concernées, et un bandeau déjà annoncé par un parent non plus.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const FORMULAIRES = [
  'components/tasks/TaskForm.tsx',
  'components/calendar/EventForm.tsx',
  'components/memory/ContactModal.tsx',
  'components/memory/ProjectModal.tsx',
  'components/guided/CreateCommandForm.tsx',
];

/** Les blocs `{error && (` … et la balise ouvrante qui suit. */
function bandeauxDErreur(code: string): string[] {
  const lignes = code.split('\n');
  const bandeaux: string[] = [];
  lignes.forEach((ligne, i) => {
    if (!/\{\s*error\s*&&\s*\(/.test(ligne)) return;
    const suivante = lignes.slice(i + 1, i + 3).join(' ');
    if (suivante.includes('bg-error/10')) bandeaux.push(suivante);
  });
  return bandeaux;
}

describe('Une erreur affichée après une action est annoncée', () => {
  it.each(FORMULAIRES)('%s annonce son échec', (fichier) => {
    const code = readFileSync(path.join(__dirname, '..', fichier), 'utf8');
    const bandeaux = bandeauxDErreur(code);
    expect(bandeaux.length, `${fichier} : aucun bandeau d'erreur repéré`).toBeGreaterThan(0);
    for (const bandeau of bandeaux) {
      expect(bandeau, `${fichier} : bandeau muet`).toMatch(/role="alert"|aria-live=/);
    }
  });
});
