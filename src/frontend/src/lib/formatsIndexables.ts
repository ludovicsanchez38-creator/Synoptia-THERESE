/**
 * Les formats que THÉRÈSE sait réellement lire — une seule liste.
 *
 * Revue du 13/08/2026, finding majeur : trois listes de formats coexistaient
 * sans source commune, et elles avaient divergé.
 *
 * - Le backend (`path_security.INDEXABLE_EXTENSIONS`) fait autorité : c'est lui
 *   qui accepte ou refuse.
 * - L'explorateur de fichiers avait la sienne, plus courte : elle cachait des
 *   formats parfaitement lisibles et proposait encore `.doc`, que le backend
 *   refuse désormais. L'utilisateur cliquait, l'indexation échouait.
 * - Le sélecteur de pièce jointe du chat en avait une troisième, avec un filtre
 *   « Images » alors qu'aucune image n'est indexable.
 *
 * Ajouter une capacité que la surface principale continue de cacher ne sert à
 * personne. Cette liste est donc l'unique référence côté interface, et un test
 * la confronte au fichier Python pour qu'elles ne puissent plus se séparer.
 */

/** Documents bureautiques et texte, ce que l'utilisateur reconnaît en premier. */
const DOCUMENTS = [
  '.txt', '.md', '.markdown', '.rst', '.log',
  '.pdf', '.docx', '.xlsx', '.pptx',
  '.csv', '.tsv',
] as const;

/** Fichiers de configuration et de balisage, lisibles comme du texte. */
const CONFIGURATION = [
  '.json', '.yaml', '.yml', '.toml', '.xml',
  '.ini', '.cfg', '.conf',
  '.tex', '.org',
] as const;

/** Code source. */
const CODE = [
  '.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.scss',
  '.java', '.c', '.cpp', '.h', '.hpp', '.rs', '.go', '.rb', '.php',
  '.swift', '.kt', '.scala', '.r', '.sql', '.sh', '.bash', '.zsh',
] as const;

export const EXTENSIONS_INDEXABLES: readonly string[] = [
  ...DOCUMENTS,
  ...CONFIGURATION,
  ...CODE,
];

/** Un fichier peut-il être indexé, d'après son extension ? */
export function estIndexable(extension?: string | null): boolean {
  if (!extension) return false;
  const normalisee = extension.startsWith('.')
    ? extension.toLowerCase()
    : `.${extension.toLowerCase()}`;
  return EXTENSIONS_INDEXABLES.includes(normalisee);
}

/**
 * Filtres du sélecteur de fichier natif, groupés comme l'utilisateur les pense.
 *
 * Aucun filtre « Images » : rien de ce que produit un appareil photo n'est
 * indexable, et le proposer menait à un échec dont la cause n'était pas
 * affichée.
 */
export const FILTRES_SELECTEUR = [
  { name: 'Documents', extensions: DOCUMENTS.map((e) => e.slice(1)) },
  { name: 'Configuration et données', extensions: CONFIGURATION.map((e) => e.slice(1)) },
  { name: 'Code source', extensions: CODE.map((e) => e.slice(1)) },
] as const;

/** Valeur de l'attribut `accept` d'un `<input type="file">`. */
export const ACCEPT_FICHIERS = EXTENSIONS_INDEXABLES.join(',');
