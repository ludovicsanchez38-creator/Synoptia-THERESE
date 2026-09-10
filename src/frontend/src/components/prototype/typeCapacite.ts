/**
 * Type affiché sur une carte du catalogue (lot 3 DA).
 * Suit `chooseCapability` : un `scenario` ouvre un parcours (P-069).
 */
import type { CapabilityGroupId, CapabilityItem } from './CapabilityCenter';

export type TypeCapacite = 'Demande relue' | 'Action' | 'Parcours' | 'Vue';

export const CLASSES_GROUPE_CAPACITE: Record<CapabilityGroupId, string> = {
  organize: 'bg-domaine-agenda-tint text-domaine-agenda',
  business: 'bg-domaine-factures-tint text-domaine-factures',
  create: 'bg-domaine-taches-tint text-domaine-taches',
  decide: 'bg-domaine-prospects-tint text-domaine-prospects',
  automate: 'bg-[var(--color-success-tint)] text-success',
  control: 'bg-surface-2 text-text-muted',
};

export function typeCapacite(item: CapabilityItem): TypeCapacite {
  if (item.destination?.kind === 'prompt') return 'Demande relue';
  if (item.destination?.kind === 'follow-ups') return 'Action';
  if (item.destination?.kind === 'action' && item.destination.action === 'guided.open') return 'Action';
  if (item.scenario) return 'Parcours';
  return 'Vue';
}

export function classesTypeCapacite(type: TypeCapacite): string {
  if (type === 'Demande relue') return 'text-sm font-semibold text-accent';
  return 'text-sm font-semibold uppercase tracking-wider text-text-muted';
}
