/**
 * Les huit étapes du pipeline (0.66.1, « Perdu » depuis P-132). Module sans
 * composant : les libellés et le domaine d'étiquette sont partagés entre la
 * vue et le formulaire. Même ordre et mêmes mots que `LIBELLES_ETAPES` côté
 * moteur (src/backend/app/services/crm_utils.py).
 */
import type { DomaineEtiquette, TonEtiquette } from '../ui/Etiquette';

export const PIPELINE_ETAPES = [
  { id: 'contact', label: 'Contact' },
  { id: 'discovery', label: 'Découverte' },
  { id: 'proposition', label: 'Proposition' },
  { id: 'signature', label: 'Signature' },
  { id: 'delivery', label: 'Livraison' },
  { id: 'active', label: 'Actif' },
  // P-132 : une vente perdue n'est plus rangée en Archive (terminé, ou fiche
  // effacée au titre du RGPD). Les deux issues terminales ferment la grille.
  { id: 'lost', label: 'Perdu' },
  { id: 'archive', label: 'Archive' },
] as const;

export type IdEtapePipeline = (typeof PIPELINE_ETAPES)[number]['id'];

/** L'explication du score, une seule phrase pour la carte du Pipeline et la fiche (P-144). */
export const SCORE_AIDE =
  "Score de potentiel commercial, calculé depuis les informations du contact et son étape dans le pipeline. Plus il est haut, plus le prospect est chaud. L'échelle n'est pas plafonnée.";

/** B-1385 : le libellé de colonne d'une étape ; un identifiant inconnu reste tel quel. */
export function libelleDEtape(id: string): string {
  return PIPELINE_ETAPES.find((e) => e.id === id)?.label ?? id;
}

export function etiquetteDEtape(id: string): {
  domaine?: DomaineEtiquette;
  ton?: TonEtiquette;
} {
  if (id === 'delivery') return { domaine: 'agenda' };
  if (id === 'active') return { ton: 'succes' };
  // P-132 : une vente perdue n'est pas une erreur ; le mot porte le sens.
  if (id === 'lost' || id === 'archive') return { ton: 'neutre' };
  return { domaine: 'prospects' };
}
