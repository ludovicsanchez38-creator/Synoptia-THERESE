/**
 * P-151 : le nom de la personne liée à une tâche (P-134), lu dans le carnet
 * de contacts déjà chargé. Sans contact connu, rien : aucun nom inventé.
 */
import type { Contact } from '../../services/api';
import { contactDisplayName } from '../prototype/prototypeReadModels';

export function nomDeLaPersonneLiee(contacts: Contact[], contactId: string | null | undefined): string | null {
  if (!contactId) return null;
  const contact = contacts.find((c) => c.id === contactId);
  return contact ? contactDisplayName(contact) : null;
}
