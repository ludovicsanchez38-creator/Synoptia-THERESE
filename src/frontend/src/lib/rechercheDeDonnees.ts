/**
 * P-016 : « un consultant retrouve son client par son nom, quelque part ».
 * La palette (⌘K) cherche aussi dans les données déjà lues par l'application :
 * contacts, projets et conversations (titre et messages chargés). Accents et
 * casse repliés, comme le tiroir (B-1352) et la liste des contacts (B-1350).
 * Rien n'est envoyé au moteur ni à un service : c'est une recherche locale.
 */
import type { Contact, Project } from '../services/api/memory';
import type { Conversation } from '../stores/chatStore';
import { contactMatchesQuery } from '../stores/contactsStore';
import { replierPourRecherche } from './replierPourRecherche';

export type ResultatDeDonnee =
  | { kind: 'contact'; id: string; titre: string; detail: string }
  | { kind: 'projet'; id: string; titre: string; detail: string }
  | { kind: 'conversation'; id: string; titre: string; detail: string };

export interface ResultatsDeDonnees {
  contacts: ResultatDeDonnee[];
  projets: ResultatDeDonnee[];
  conversations: ResultatDeDonnee[];
}

export const AUCUN_RESULTAT_DE_DONNEES: ResultatsDeDonnees = { contacts: [], projets: [], conversations: [] };

const PLAFONDS = { contacts: 5, projets: 3, conversations: 5 };

export function chercherDansLesDonnees(
  recherche: string,
  sources: { contacts: readonly Contact[]; projets: readonly Project[]; conversations: readonly Conversation[] },
): ResultatsDeDonnees {
  const terme = recherche.trim();
  const replie = replierPourRecherche(terme);
  if (!replie) return AUCUN_RESULTAT_DE_DONNEES;

  const contacts = sources.contacts
    .filter((contact) => contactMatchesQuery(contact, terme))
    .slice(0, PLAFONDS.contacts)
    .map((contact): ResultatDeDonnee => ({
      kind: 'contact',
      id: contact.id,
      titre: [contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.company || contact.email || 'Sans nom',
      detail: [contact.company, contact.email].filter(Boolean).join(' · ') || 'Contact',
    }));

  const projets = sources.projets
    .filter((projet) => replierPourRecherche(
      [projet.name, projet.description ?? '', ...(projet.tags ?? [])].join(' '),
    ).includes(replie))
    .slice(0, PLAFONDS.projets)
    .map((projet): ResultatDeDonnee => ({
      kind: 'projet',
      id: projet.id,
      titre: projet.name,
      detail: projet.description || 'Projet',
    }));

  // B-1440 : une conversation se retrouve aussi par le nom de son projet
  // (comme dans le tiroir, P-127), et le résultat le nomme.
  const nomDuProjet = new Map(sources.projets.map((projet) => [projet.id, projet.name]));
  const conversations = sources.conversations
    .filter((conversation) => replierPourRecherche([
      conversation.title,
      conversation.projectId ? nomDuProjet.get(conversation.projectId) ?? '' : '',
      ...(conversation.messages ?? []).map((message) => message.content ?? ''),
    ].join('\n')).includes(replie))
    .slice(0, PLAFONDS.conversations)
    .map((conversation): ResultatDeDonnee => {
      const projet = conversation.projectId ? nomDuProjet.get(conversation.projectId) : undefined;
      return {
        kind: 'conversation',
        id: conversation.id,
        titre: conversation.title || 'Nouvelle conversation',
        detail: projet ? `Conversation · Projet : ${projet}` : 'Conversation',
      };
    });

  return { contacts, projets, conversations };
}
