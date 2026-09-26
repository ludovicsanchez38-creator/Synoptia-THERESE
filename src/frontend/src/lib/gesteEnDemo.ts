/**
 * B-1621 (décision de Ludo, 26/09) : en mode démo, les gestes destructifs
 * (supprimer, anonymiser, déplacer) sont bloqués. La démo affiche des
 * pseudonymes ; ces gestes agiraient sur la vraie fiche.
 */
import { useDemoStore } from '../stores/demoStore';
import { useStatusStore } from '../stores/statusStore';

export const MESSAGE_GESTE_EN_DEMO = 'Désactivé en mode démo : ce geste agirait sur tes vraies données.';

/** Vrai si le geste est bloqué (et la raison annoncée). */
export function gesteBloqueEnDemo(): boolean {
  if (!useDemoStore.getState().enabled) return false;
  useStatusStore.getState().addNotification({ type: 'info', title: 'Mode démo', message: MESSAGE_GESTE_EN_DEMO });
  return true;
}
