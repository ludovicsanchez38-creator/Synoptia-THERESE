/**
 * B-1399 : un refus 422 dit quel champ et quelle règle, en français.
 *
 * Le moteur renvoie `details: [{field, message}]` (messages Pydantic, en
 * anglais) ; l'écran n'affichait que « Données invalides dans la requête ».
 */
const LIBELLES_DE_CHAMP: Record<string, string> = {
  first_name: 'Prénom',
  last_name: 'Nom',
  name: 'Nom',
  company: 'Entreprise',
  email: 'E-mail',
  phone: 'Téléphone',
  address: 'Adresse',
  notes: 'Notes',
  tags: 'Étiquettes',
  title: 'Titre',
  description: 'Description',
  brief: 'Brief',
  budget: 'Budget',
  quantity: 'Quantité',
  unit_price_ht: 'Prix HT',
  due_date: 'Échéance',
  start_datetime: 'Début',
  end_datetime: 'Fin',
  summary: 'Titre',
  location: 'Lieu',
};

function regleEnFrancais(message: string): string {
  let m: RegExpExecArray | null;
  if ((m = /at most (\d+) characters?/i.exec(message))) return `${m[1]} caractères au maximum`;
  if ((m = /at least (\d+) characters?/i.exec(message))) return `au moins ${m[1]} caractères`;
  if (/^Field required$/i.test(message)) return 'obligatoire';
  if (/valid email/i.test(message)) return 'adresse e-mail invalide';
  if ((m = /greater than or equal to ([-\d.,]+)/i.exec(message))) return `doit être supérieur ou égal à ${m[1]}`;
  if ((m = /greater than ([-\d.,]+)/i.exec(message))) return `doit être supérieur à ${m[1]}`;
  if ((m = /less than or equal to ([-\d.,]+)/i.exec(message))) return `doit être inférieur ou égal à ${m[1]}`;
  if (/valid (number|integer)/i.test(message)) return 'nombre attendu';
  if (/valid (date|datetime)/i.test(message)) return 'date invalide';
  return message;
}

/** Le message d'un refus 422, ou `null` quand le moteur n'a pas donné de détail. */
export function messageDeValidation(details: unknown): string | null {
  if (!Array.isArray(details) || details.length === 0) return null;
  const phrases = details
    .filter((d): d is { field?: unknown; message?: unknown } => typeof d === 'object' && d !== null)
    .map((d) => {
      const champ = String(d.field ?? '').split('.').pop() || '';
      const libelle = LIBELLES_DE_CHAMP[champ] ?? champ;
      const regle = regleEnFrancais(String(d.message ?? ''));
      return libelle ? `${libelle} : ${regle}.` : `${regle}.`;
    });
  return phrases.length ? phrases.join(' ') : null;
}
