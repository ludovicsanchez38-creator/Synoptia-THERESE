/** P-159 : messages passés relus, et ceux encore là après la coupe du modèle. */
export interface ContexteTransmis {
  messages_relus: number;
  messages_transmis: number;
}

function compteMessages(n: number): string {
  if (n <= 0) return 'aucun message';
  if (n === 1) return '1 message';
  return `${n} messages`;
}

/** Texte court sous la réponse. Les deux comptes égaux : tout a été relu. */
export function texteContexteTransmis(contexte: ContexteTransmis): string {
  const relus = contexte.messages_relus;
  const transmis = contexte.messages_transmis;
  if (transmis >= relus) {
    if (relus <= 0) return 'Contexte : aucun message relu';
    if (relus === 1) return 'Contexte : 1 message relu';
    return `Contexte : ${relus} messages relus`;
  }
  return `Contexte raccourci : ${compteMessages(transmis)} sur ${relus}`;
}
