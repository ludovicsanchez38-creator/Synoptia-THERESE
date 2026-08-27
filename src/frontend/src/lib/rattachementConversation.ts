/**
 * Rattacher une conversation à un projet, même avant son premier message.
 *
 * Une conversation neuve n'existe qu'en local : son identifiant est fabriqué
 * côté client et la ligne en base n'apparaît qu'au premier message envoyé.
 * Choisir un projet avant cela répondait 404, et le geste se défaisait tout
 * seul — au moment précis où l'on en a le plus besoin, juste après avoir
 * indexé un dossier.
 *
 * On persiste donc la conversation quand l'utilisateur rattache réellement un
 * projet. C'est un geste intentionnel, et la conversation serait de toute
 * façon enregistrée au premier message.
 *
 * Deux réserves tenues ici :
 *   - une conversation éphémère ne doit jamais être persistée ; on refuse, en
 *     le disant, plutôt que d'en faire une conversation ordinaire dans le dos
 *     de l'utilisateur ;
 *   - revenir aux documents généraux ne persiste rien : ce serait créer une
 *     conversation vide pour un réglage qui est déjà le défaut.
 */
import { createConversation, setConversationProject } from '../services/api';
import { useChatStore } from '../stores/chatStore';

export class ConversationEphemereError extends Error {
  constructor() {
    super('Une conversation éphémère ne peut pas être rattachée à un projet.');
    this.name = 'ConversationEphemereError';
  }
}

/** L'identifiant réellement connu du serveur, en persistant la conversation si besoin. */
export async function assurerConversationPersistee(conversationId: string): Promise<string> {
  const etat = useChatStore.getState();
  const conversation = etat.conversations.find((c) => c.id === conversationId);

  // Conversation inconnue du store (surface isolée, test) : on la suppose déjà
  // enregistrée, et l'appel suivant dira le contraire si ce n'est pas le cas.
  if (!conversation) return conversationId;
  if (conversation.synced) return conversationId;
  if (conversation.ephemeral) throw new ConversationEphemereError();

  const creee = await createConversation(conversation.title);
  etat.updateConversationId(conversationId, creee.id);
  return creee.id;
}

/** Rattache la conversation à un projet, en la persistant d'abord si nécessaire. */
export async function rattacherAUnProjet(
  conversationId: string,
  projectId: string | null,
  memoryScope: string
): Promise<string> {
  // Le retour aux documents généraux ne justifie pas de créer une ligne en base.
  const identifiant =
    projectId === null && memoryScope === 'global'
      ? conversationId
      : await assurerConversationPersistee(conversationId);

  await setConversationProject(identifiant, projectId, memoryScope);
  return identifiant;
}
