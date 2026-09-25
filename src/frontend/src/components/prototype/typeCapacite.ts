/**
 * Type affiché sur une carte du catalogue (lot 3 DA).
 * Ordre § 3.1 ; sur le catalogue actuel aucun id n'a les deux.
 */
import type { CapabilityGroupId, CapabilityItem } from './CapabilityCenter';

// P-098 : « Action » a rejoint « Vue » : ces cartes s'ouvrent au clic comme
// une Vue, et la légende ne l'expliquait nulle part.
export type TypeCapacite = 'Demande relue' | 'Parcours' | 'Vue';

/**
 * P-128 (Hugo, cycle 13) : ce que chaque type ouvre. Une seule source pour la
 * légende du Centre et l'infobulle du badge.
 */
export const EXPLICATION_DU_TYPE: Record<TypeCapacite, string> = {
  Vue: 'Vue : ouvre un écran au clic (par exemple Tâches).',
  Parcours: 'Parcours : ouvre au clic un mode guidé de l’Accueil (par exemple Préparer un rendez-vous).',
  'Demande relue': 'Demande relue : pose une phrase dans le champ, que tu relis avant l’envoi.',
};

export const CLASSES_GROUPE_CAPACITE: Record<CapabilityGroupId, string> = {
  organize: 'bg-domaine-agenda-tint text-domaine-agenda',
  business: 'bg-domaine-factures-tint text-domaine-factures',
  create: 'bg-domaine-taches-tint text-domaine-taches',
  decide: 'bg-domaine-prospects-tint text-domaine-prospects',
  automate: 'bg-[var(--color-success-tint)] text-success',
  control: 'bg-surface-2 text-text-muted',
};

// Audit de release 0.75 : ces actions posent une phrase dans le composeur
// (actionRegistry : insertChatPrompt), comme une destination « prompt ».
const ACTIONS_QUI_POSENT_UNE_PHRASE = new Set(['guided.open']);

export function typeCapacite(item: CapabilityItem): TypeCapacite {
  if (item.destination?.kind === 'prompt') return 'Demande relue';
  if (item.destination?.kind === 'action' && ACTIONS_QUI_POSENT_UNE_PHRASE.has(item.destination.action)) {
    return 'Demande relue';
  }
  if (item.scenario) return 'Parcours';
  return 'Vue';
}

export function classesTypeCapacite(type: TypeCapacite): string {
  if (type === 'Demande relue') return 'text-sm font-semibold text-accent';
  return 'text-sm font-semibold uppercase tracking-wider text-text-muted';
}
