import { nomDeLaDestination, type Destination } from '../../lib/destinations';

/**
 * Le bouton qui quitte une carte pour ouvrir la vue complète correspondante.
 *
 * Campagne dix personas, persona 08 et retour de Dr_logic-3D :
 *
 *   « je ne peux pas deviner que "vue complète" pointe sur l'agenda, de la
 *     même manière que : aide -> quotidien -> agenda -> voir tout mon agenda
 *     -> agenda. Donc en cas de bug, je ne sais pas à quoi m'attendre, ni
 *     comment y faire référence de manière explicite dans ce chat. »
 *
 * Sept cartes portaient sept formulations pour le même geste - « Vue complète »
 * (deux fois, pour deux destinations différentes), « Voir tout mon agenda »,
 * « Gérer mes contacts », « Email complet », « Facturation complète »… Aucune
 * ne nommait sa destination avec le nom que cette destination porte.
 *
 * Le libellé DÉRIVE désormais de `viewLabels`, la table que la vue elle-même
 * utilise pour son titre. Renommer une vue renomme le bouton : le vocabulaire
 * ne peut plus diverger, et il n'y a rien à se souvenir de mettre à jour.
 */
export function BoutonOuvrirLaVue({
  vue,
  onOuvrir,
  className,
}: {
  vue: Destination;
  onOuvrir: () => void;
  className?: string;
}) {
  const nom = nomDeLaDestination(vue);
  return (
    <button
      type="button"
      onClick={onOuvrir}
      aria-label={`Ouvrir ${nom}`}
      className={
        className ??
        'rounded-sm border border-border px-2.5 py-1.5 text-xs font-semibold text-text hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent'
      }
    >
      Ouvrir {nom}
    </button>
  );
}
