/**
 * Texte brut d'un message email, dérivé du HTML quand le texte manque.
 */
// B-495 : un message HTML seul (body_plain vide) partait en transfert avec un
// corps vide, et la citation retombait sur l'extrait tronqué. Le texte se
// dérive du HTML quand le texte brut manque.
export function texteDuCorps(message: {
  body_plain: string | null;
  body_html: string | null;
  snippet?: string | null;
}): string {
  if (message.body_plain?.trim()) return message.body_plain;
  if (message.body_html) {
    const doc = new DOMParser().parseFromString(message.body_html, 'text/html');
    doc.body.querySelectorAll('script, style, head').forEach((n) => n.remove());
    doc.body.querySelectorAll('br').forEach((n) => n.replaceWith('\n'));
    doc.body
      .querySelectorAll('p, div, li, tr, h1, h2, h3, h4, h5, h6, blockquote, pre')
      .forEach((n) => n.append('\n'));
    const texte = (doc.body.textContent ?? '')
      .replace(/[ \t]+\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
    if (texte) return texte;
  }
  return message.snippet || '';
}
