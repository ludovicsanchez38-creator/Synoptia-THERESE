/**
 * B-066 — le gabarit d'environnement ne documente que des variables lues.
 *
 * Constat du 02/09/2026 : `.env.example` documentait
 * `VITE_THERESE_INTERFACE_MODE=classic` (domaine « classic |
 * conversation-canvas », avec la promesse que les builds distribuables forcent
 * « classic »). Le nom n'apparaissait dans AUCUN fichier de code : son lecteur
 * historique, `interfaceMode.ts`, avait disparu avec le mode classique, et
 * `App.tsx` monte `<ConversationCanvasPrototype />` sans condition. Le gabarit
 * n'était donc pas seulement mort : il annonçait un défaut (« classic ») qui
 * n'existe plus, et un développeur qui basculait la valeur croyait changer
 * d'interface alors qu'il obtenait déjà le canevas.
 *
 * Le test verrouille le lien dans le sens qui compte : toute variable `VITE_`
 * écrite dans le gabarit doit être lue quelque part par le code. Une variable
 * retirée du code doit disparaître du gabarit avec lui.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const racineFront = join(__dirname, '..', '..');
const gabarit = readFileSync(join(racineFront, '.env.example'), 'utf-8');

/** Les clés `VITE_*` réellement affectées dans le gabarit (hors commentaires). */
function clesDuGabarit(contenu: string): string[] {
  return contenu
    .split('\n')
    .map((ligne) => /^\s*([A-Z_][A-Z0-9_]*)\s*=/.exec(ligne))
    .filter((trouve): trouve is RegExpExecArray => trouve !== null)
    .map((trouve) => trouve[1])
    .filter((cle) => cle.startsWith('VITE_'));
}

/** Sources de l'application, tests exclus : un test qui cite une variable ne
 *  prouve pas qu'elle gouverne quoi que ce soit. */
function sourcesApplicatives(dossier: string, accumulateur: string[] = []): string[] {
  for (const entree of readdirSync(dossier)) {
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) {
      if (entree === 'test' || entree === '__mocks__') continue;
      sourcesApplicatives(chemin, accumulateur);
      continue;
    }
    if (!/\.(ts|tsx)$/.test(entree)) continue;
    if (/\.(test|spec)\.tsx?$/.test(entree)) continue;
    accumulateur.push(chemin);
  }
  return accumulateur;
}

const sources = sourcesApplicatives(join(racineFront, 'src')).map((chemin) => readFileSync(chemin, 'utf-8'));

describe('B-066 — toute variable documentée dans .env.example est lue par le code', () => {
  it('le gabarit documente au moins une variable', () => {
    // Sans cette borne, vider le fichier rendrait le test vert sans rien prouver.
    expect(clesDuGabarit(gabarit).length).toBeGreaterThanOrEqual(1);
  });

  it('chaque clé VITE_ du gabarit apparaît dans un import.meta.env du code', () => {
    const mortes = clesDuGabarit(gabarit).filter(
      (cle) => !sources.some((source) => source.includes(`import.meta.env.${cle}`)),
    );
    expect(
      mortes,
      `variable(s) documentée(s) mais lue(s) nulle part : ${mortes.join(', ')}`,
    ).toEqual([]);
  });
});
