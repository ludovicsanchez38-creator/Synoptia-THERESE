/**
 * Qui décide de l'identifiant d'une conversation.
 *
 * Une conversation naît en local, avec un identifiant fabriqué côté client.
 * Elle en reçoit un du serveur au premier message — ou plus tôt, si
 * l'utilisateur rattache un projet, ce qui la persiste (voir
 * `rattachementConversation`).
 *
 * Les deux chemins peuvent se croiser. Un envoi parti juste avant le
 * rattachement n'avait pas encore d'identifiant à transmettre : le backend en
 * crée une SECONDE, et le flux la renvoie. L'adopter écraserait la
 * conversation qu'on vient de rattacher, et le projet posé côté serveur
 * resterait sur une conversation que plus personne n'affiche.
 *
 * Règle : une conversation qui a déjà une identité serveur la garde.
 */
export function doitAdopterIdentiteServeur(
  identifiantLocal: string | null | undefined,
  identifiantServeur: string | null | undefined,
  dejaEnregistree: boolean
): boolean {
  if (!identifiantLocal || !identifiantServeur) return false;
  if (identifiantLocal === identifiantServeur) return false;
  return !dejaEnregistree;
}
