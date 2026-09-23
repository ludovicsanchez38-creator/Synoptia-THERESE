/**
 * THÉRÈSE v2 - Une surface de la coque recouvre-t-elle ce qu'on est en train de faire ?
 *
 * B-980 : un formulaire en cours de saisie inscrit son Échap dans la pile
 * (escapeStack). Les Réglages, les fiches, le Board, l'Atelier, la palette ou
 * les centres de la coque n'y sont pas : ils s'ouvrent par-dessus sans se
 * signaler. Tant que l'une de ces surfaces est ouverte, le formulaire en
 * dessous doit laisser passer Échap pour que la coque la ferme.
 */
import { useActionsStore } from '../stores/actionsStore';
import { useAtelierStore } from '../stores/atelierStore';
import { usePanelStore } from '../stores/panelStore';

/** Une surface pilotée par un store de la coque est ouverte. */
export function uneSurfaceDeLaCoqueEstOuverte(): boolean {
  const ps = usePanelStore.getState();
  return Boolean(
    ps.showSaveCommand || ps.showContactModal || ps.showProjectModal || ps.showBoardPanel
    || ps.showShortcuts || ps.showSettings || ps.showPromptLibrary
    || useAtelierStore.getState().isOpen || useActionsStore.getState().isPanelOpen,
  );
}

/**
 * Une modale (`aria-modal`) sans lien avec `racine` est ouverte : ni elle ne
 * la contient (le panneau qui héberge le formulaire), ni `racine` ne la
 * contient (un dialogue du formulaire lui-même). Couvre les surfaces en état
 * local de la coque (palette de commandes, centres).
 */
export function uneModaleDistincteEstOuverte(racine: Element | null): boolean {
  if (!racine || typeof document === 'undefined') return false;
  return Array.from(document.querySelectorAll('[aria-modal="true"]'))
    .some((modale) => !modale.contains(racine) && !racine.contains(modale));
}
