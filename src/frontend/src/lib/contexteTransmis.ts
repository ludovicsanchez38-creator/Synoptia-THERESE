/** P-159 : messages passés relus, et ceux encore là après la coupe du modèle. */
export interface ContexteTransmis {
  messages_relus: number;
  messages_transmis: number;
  /** Caractères du message en cours retirés pour tenir dans le modèle. */
  caracteres_retires?: number;
}

function compteMessages(n: number): string {
  if (n <= 0) return 'aucun message';
  if (n === 1) return '1 message';
  return `${n} messages`;
}

function phraseMessageRaccourci(retire: number | undefined): string {
  if (!retire || retire <= 0) return '';
  const quantite = retire === 1 ? '1 caractère retiré' : `${retire} caractères retirés`;
  return `Ton message a été raccourci pour tenir dans le modèle (${quantite}).`;
}

/** Texte court sous la réponse. Les deux comptes égaux : tout a été relu. */
export function texteContexteTransmis(contexte: ContexteTransmis): string {
  const relus = contexte.messages_relus;
  const transmis = contexte.messages_transmis;
  let base: string;
  if (transmis >= relus) {
    if (relus <= 0) base = 'Contexte : aucun message relu';
    else if (relus === 1) base = 'Contexte : 1 message relu';
    else base = `Contexte : ${relus} messages relus`;
  } else {
    base = `Contexte raccourci : ${compteMessages(transmis)} sur ${relus}`;
  }
  const suite = phraseMessageRaccourci(contexte.caracteres_retires);
  if (!suite) return base;
  if (relus <= 0 && transmis <= 0) return suite;
  return `${base}. ${suite}`;
}
