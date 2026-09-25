import type { TodayAttentionItem } from '../components/prototype/prototypeReadModels';
import type { AppView } from '../stores/navigationStore';

export type CibleDUnPoint =
  | { kind: 'invoice'; id: string }
  | { kind: 'contact'; id: string }
  | { kind: 'view'; view: AppView };

/** B-563 (05/09/2026) : un point d'attention nommé ouvre l'objet précis quand on le connaît. */
export function destinationDuPoint(item: TodayAttentionItem): CibleDUnPoint {
  if (item.kind === 'invoice' && item.cibleId) return { kind: 'invoice', id: item.cibleId };
  // P-134 : un point qui nomme une personne ouvre sa fiche (son numéro).
  if (item.contactId) return { kind: 'contact', id: item.contactId };
  return { kind: 'view', view: item.targetView };
}
