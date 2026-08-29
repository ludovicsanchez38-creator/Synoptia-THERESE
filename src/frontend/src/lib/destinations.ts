import type { AppView } from '../stores/navigationStore';
import { viewLabels } from '../components/prototype/PrototypeUnifiedViewCanvas';

/**
 * Les deux panneaux qui ne sont pas des « vues » au sens de la navigation, mais
 * qui sont bien des destinations pour l'utilisateur. Leurs noms sont ceux que
 * l'écran affiche déjà (`BoardPanel` aria-label, liste des raccourcis).
 */
const NOMS_DES_PANNEAUX = { board: 'Décision', atelier: 'Améliorer THÉRÈSE' } as const;

export type Destination = Exclude<AppView, 'chat'> | keyof typeof NOMS_DES_PANNEAUX;

export function nomDeLaDestination(destination: Destination): string {
  return destination in NOMS_DES_PANNEAUX
    ? NOMS_DES_PANNEAUX[destination as keyof typeof NOMS_DES_PANNEAUX]
    : viewLabels[destination as Exclude<AppView, 'chat'>];
}
