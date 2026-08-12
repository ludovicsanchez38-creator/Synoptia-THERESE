/**
 * La fiche des raccourcis ne doit annoncer que des raccourcis qui existent.
 *
 * Inventaire des capacités du 13/08/2026 : quatre raccourcis étaient annoncés
 * sans aucun gestionnaire dans le code (⌘⌫ « Effacer la conversation »,
 * ⌘⇧P « Nouveau projet », ⌘⇧O « Ouvrir un dossier », ⌘S « Sauvegarder »), et
 * deux raccourcis réels et fonctionnels n'y figuraient pas (⌘, pour les
 * Paramètres, ⌘⇧D pour le mode démonstration — ce dernier n'ayant aucun autre
 * chemin d'accès).
 *
 * Une fiche d'aide qui ment est pire que pas de fiche : l'utilisateur essaie,
 * rien ne se passe, et il conclut que l'application est cassée.
 *
 * Le test lit le code du gestionnaire de clavier et vérifie que chaque touche
 * annoncée y est réellement traitée. Il ne remplace pas une source unique — ce
 * sera l'objet du manifeste de capacités — mais il empêche la dérive d'ici là.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { SHORTCUT_GROUPS } from './ShortcutsModal';

const ici = dirname(fileURLToPath(import.meta.url));
const sourceDuHook = readFileSync(
  resolve(ici, '../../hooks/useKeyboardShortcuts.ts'),
  'utf-8',
);

/** Touches gérées ailleurs que dans le hook (composeur, navigateur). */
const HORS_HOOK = new Set(['↵', '⇧ + ↵']);

/** Traduit « ⌘ + ⇧ + C » en la condition qu'on doit trouver dans le hook. */
function toucheDe(raccourci: string): string | null {
  const dernier = raccourci.split('+').pop()?.trim() ?? '';
  if (dernier === 'Échap') return 'escape';
  if (dernier === ',') return ',';
  if (dernier === '/') return '/';
  if (/^[A-Z]$/.test(dernier)) return dernier.toLowerCase();
  return null;
}

describe('la fiche des raccourcis dit la vérité', () => {
  const annonces = SHORTCUT_GROUPS.flatMap((g) =>
    g.shortcuts.map((s) => ({ ...s, groupe: g.title })),
  );

  it('annonce au moins une vingtaine de raccourcis', () => {
    expect(annonces.length).toBeGreaterThan(15);
  });

  it.each(annonces.filter((s) => !HORS_HOOK.has(s.keys)))(
    'le raccourci $keys ($description) a un gestionnaire',
    ({ keys, description }) => {
      const touche = toucheDe(keys);
      expect(touche, `touche non interprétable : ${keys}`).not.toBeNull();

      const traitee =
        sourceDuHook.includes(`=== '${touche}'`) ||
        sourceDuHook.includes(`key === '${touche}'`);

      expect(
        traitee,
        `« ${description} » (${keys}) est annoncé à l'utilisateur mais aucun ` +
          `gestionnaire ne traite cette touche : il essaiera, rien ne se passera`,
      ).toBe(true);
    },
  );

  it('annonce les raccourcis réels qui étaient tus', () => {
    const touches = annonces.map((s) => s.keys);

    // ⌘⇧D n'a aucun autre chemin d'accès que ce raccourci : le taire le rendait
    // inatteignable.
    expect(touches).toContain('⌘ + ⇧ + D');
    expect(touches).toContain('⌘ + ,');
  });
});
