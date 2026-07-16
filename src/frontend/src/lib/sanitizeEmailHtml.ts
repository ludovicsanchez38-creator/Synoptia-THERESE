import DOMPurify from 'dompurify';

/**
 * Sanitise le HTML d'un email ou d'une signature avant rendu.
 *
 * 1. DOMPurify neutralise scripts, event handlers et vecteurs XSS.
 * 2. Interdit <style> ET l'attribut `style` : le CSS inline permet l'exfiltration
 *    réseau (background-image:url(http://...)) et les overlays (position:fixed),
 *    contraires à la promesse « 100 % local ».
 * 3. Supprime les <link stylesheet> résiduels.
 *
 * Politique UNIQUE partagée par l'affichage des emails reçus (EmailDetail) et
 * l'aperçu d'édition de signature (SignatureEditorModal), cohérente avec le
 * sanitizer backend nh3 (qui n'autorise pas non plus l'attribut style).
 */
export function sanitizeEmailHtml(
  html: string,
  options: { allowRemoteImages?: boolean } = {},
): string {
  const purified = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'div', 'span',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'dl', 'dt', 'dd',
      'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
      'img', 'blockquote', 'pre', 'code', 'hr', 'sup', 'sub', 'small',
      'figure', 'figcaption', 'abbr', 'address', 'details', 'summary',
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'class', 'id', 'width', 'height',
      'colspan', 'rowspan', 'cellpadding', 'cellspacing', 'border',
      'align', 'valign', 'target', 'rel',
    ],
    ALLOW_DATA_ATTR: false,
    ADD_ATTR: ['target'],
    FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea', 'select', 'button'],
  });
  // Supprimer les <link stylesheet> résiduels
  const withoutLinks = purified.replace(/<link[^>]*rel=["']stylesheet["'][^>]*\/?>/gi, '');

  // US-002 : par defaut on NE charge PAS les images distantes (pixels de
  // tracage, requetes reseau contraires a la promesse « 100 % local »). Les
  // images data: inline restent affichees. L'affichage des images distantes
  // est un opt-in explicite (allowRemoteImages). La CSP les bloque aussi au
  // niveau du moteur ; ceci est la defense applicative, testable hors Tauri.
  if (options.allowRemoteImages) {
    return withoutLinks;
  }
  return blockRemoteImages(withoutLinks);
}

/**
 * Neutralise les <img src="http(s)://..."> : la source distante est deplacee
 * dans data-blocked-src et retiree, aucune requete reseau n'est declenchee.
 * Les images data: inline sont conservees.
 */
function blockRemoteImages(html: string): string {
  if (typeof DOMParser === 'undefined') return html;
  const doc = new DOMParser().parseFromString(html, 'text/html');
  let blocked = false;
  doc.querySelectorAll('img').forEach((img) => {
    const src = img.getAttribute('src') ?? '';
    if (/^https?:/i.test(src)) {
      img.setAttribute('data-blocked-src', src);
      img.removeAttribute('src');
      if (!img.getAttribute('alt')) img.setAttribute('alt', 'Image distante bloquée');
      img.setAttribute('data-remote-blocked', 'true');
      blocked = true;
    }
  });
  return blocked ? doc.body.innerHTML : html;
}
