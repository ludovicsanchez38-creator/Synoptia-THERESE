/**
 * Les sept étapes du pipeline (0.66.1). Module sans composant : les libellés
 * et le domaine d'étiquette sont partagés entre la vue et le formulaire.
 */
import type { DomaineEtiquette, TonEtiquette } from '../ui/Etiquette';

export const PIPELINE_ETAPES = [
  { id: 'contact', label: 'Contact' },
  { id: 'discovery', label: 'Découverte' },
  { id: 'proposition', label: 'Proposition' },
  { id: 'signature', label: 'Signature' },
  { id: 'delivery', label: 'Livraison' },
  { id: 'active', label: 'Actif' },
  { id: 'archive', label: 'Archive' },
] as const;

export type IdEtapePipeline = (typeof PIPELINE_ETAPES)[number]['id'];

export function etiquetteDEtape(id: string): {
  domaine?: DomaineEtiquette;
  ton?: TonEtiquette;
} {
  if (id === 'delivery') return { domaine: 'agenda' };
  if (id === 'active') return { ton: 'succes' };
  if (id === 'archive') return { ton: 'neutre' };
  return { domaine: 'prospects' };
}
