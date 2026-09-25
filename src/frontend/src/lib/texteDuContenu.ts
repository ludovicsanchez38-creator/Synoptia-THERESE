/**
 * B-1468 (recette P-146, lot 5) : un message doit toujours porter du texte.
 * Le résultat brut d'un connecteur (`{content: [{type: 'text', text}]}`) est
 * rendu par ses blocs texte ; toute autre valeur, par sa forme JSON.
 */
export function texteDuContenu(valeur: unknown): string {
  if (typeof valeur === 'string') return valeur;
  if (valeur === null || valeur === undefined) return '';
  const blocs = (valeur as { content?: unknown }).content;
  if (Array.isArray(blocs)) {
    const textes = blocs
      .filter((bloc): bloc is { type: string; text: unknown } =>
        typeof bloc === 'object' && bloc !== null && (bloc as { type?: unknown }).type === 'text')
      .map((bloc) => String(bloc.text ?? ''));
    if (textes.length > 0) return textes.join('\n');
  }
  try {
    return JSON.stringify(valeur);
  } catch {
    return String(valeur);
  }
}
