/**
 * THÉRÈSE v2 - Pile d'Échap pour overlays internes aux vues (correctif KO Syn).
 *
 * Problème : les modaux NON gérés par un store (confirmation de suppression,
 * action RGPD dans la Mémoire-vue, menu slash...) sont en state local React.
 * `resolveEscape` ne les voyait pas → Échap tombait sur le retour de vue (goBack)
 * et ÉJECTAIT la vue entière sous le modal (KO 1.1/1.2), ou fermait la sidebar
 * en plus du menu slash (KO 1.3).
 *
 * Solution : un composant qui ouvre un tel overlay PUSH un handler ici (et le POP
 * au démontage). `resolveEscape` déclenche le handler le plus en avant AVANT toute
 * autre priorité. Pile LIFO : le dernier overlay ouvert est le premier fermé.
 */

const handlers: Array<() => void> = [];

/** Enregistre un handler Échap (overlay le plus en avant). Retourne la désinscription. */
export function pushEscapeHandler(handler: () => void): () => void {
  handlers.push(handler);
  return () => {
    const i = handlers.lastIndexOf(handler);
    if (i !== -1) handlers.splice(i, 1);
  };
}

/** Déclenche le handler le plus récent s'il existe. Retourne true s'il a agi. */
export function runTopEscapeHandler(): boolean {
  const handler = handlers[handlers.length - 1];
  if (!handler) return false;
  handler();
  return true;
}

/** Réinitialise la pile (tests uniquement). */
export function _clearEscapeHandlers(): void {
  handlers.length = 0;
}
