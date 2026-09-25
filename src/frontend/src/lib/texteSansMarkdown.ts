/**
 * Texte lisible tiré d'une réponse Markdown, sur une ligne.
 *
 * B-1351 : la description d'un raccourci créé depuis une réponse du chat
 * montrait les balises (« **Compte rendu** **Cliente :** »). Retire gras,
 * italique, code, titres, citations et puces ; garde le texte des liens.
 */
export function texteSansMarkdown(markdown: string): string {
  return markdown
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/^\s{0,3}(#{1,6}|>|[-*+]|\d+[.)])\s+/gm, '')
    .replace(/\*\*|__|`+/g, '')
    .replace(/(^|\s)[*_](\S)/g, '$1$2')
    .replace(/(\S)[*_](?=\s|$|[.,;:!?])/g, '$1')
    .replace(/\s+/g, ' ')
    .trim();
}
