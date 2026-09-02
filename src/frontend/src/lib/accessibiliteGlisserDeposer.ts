/**
 * B-217 - les tableaux glisser-déposer parlent français, et nomment les objets.
 *
 * @dnd-kit sert ses textes par défaut quand on ne lui en donne pas : « To pick
 * up a draggable item, press the space bar… » pour les instructions, et des
 * annonces qui désignent l'objet déplacé par son IDENTIFIANT technique
 * (« Draggable item 3f2a-… was dropped over droppable area done »). Dans une
 * application française, c'est deux fautes à la fois : la langue, et un UUID
 * lu à voix haute à la place du nom de la tâche.
 *
 * Un seul jeu partagé par les quatre tableaux (Tâches, Projets, Pipeline,
 * Trame de document) : chacun fournit la fonction qui traduit un identifiant
 * en nom lisible - la carte comme la colonne, puisque `over.id` désigne aussi
 * bien une zone de dépôt qu'une autre carte.
 */
import type { Announcements, ScreenReaderInstructions } from '@dnd-kit/core';
import type { UniqueIdentifier } from '@dnd-kit/core';

/** Traduit un identifiant dnd-kit en nom lisible ; `null` si inconnu. */
export type LibelleParIdentifiant = (id: UniqueIdentifier) => string | null;

export const INSTRUCTIONS_GLISSER_DEPOSER: ScreenReaderInstructions = {
  draggable:
    'Pour saisir un élément, appuie sur la barre d’espace. ' +
    'Pendant le déplacement, utilise les flèches du clavier pour le déplacer. ' +
    'Appuie de nouveau sur la barre d’espace pour le déposer à sa nouvelle place, ' +
    'ou sur Échap pour annuler.',
};

/**
 * Les annonces d'un tableau, en français et par les noms.
 *
 * `libelle` reçoit l'identifiant d'une carte OU d'une zone de dépôt : les
 * deux passent par `active.id` / `over.id`. Quand il ne sait pas répondre, on
 * retombe sur une formule sans identifiant plutôt que de lire un UUID.
 */
export function annoncesGlisserDeposer(libelle: LibelleParIdentifiant): Announcements {
  const nom = (id: UniqueIdentifier | undefined): string =>
    (id === undefined ? null : libelle(id)) ?? 'l’élément';

  return {
    onDragStart: ({ active }) => `Élément saisi : ${nom(active.id)}.`,
    onDragOver: ({ active, over }) =>
      over
        ? `${nom(active.id)} est au-dessus de ${nom(over.id)}.`
        : `${nom(active.id)} n’est plus au-dessus d’une zone de dépôt.`,
    onDragEnd: ({ active, over }) =>
      over
        ? `${nom(active.id)} a été déposé sur ${nom(over.id)}.`
        : `${nom(active.id)} a été relâché sans être déposé.`,
    onDragCancel: ({ active }) =>
      `Déplacement annulé : ${nom(active.id)} retrouve sa place.`,
  };
}

/** Le bloc `accessibility` à passer tel quel à un `DndContext`. */
export function accessibiliteGlisserDeposer(libelle: LibelleParIdentifiant): {
  announcements: Announcements;
  screenReaderInstructions: ScreenReaderInstructions;
} {
  return {
    announcements: annoncesGlisserDeposer(libelle),
    screenReaderInstructions: INSTRUCTIONS_GLISSER_DEPOSER,
  };
}
