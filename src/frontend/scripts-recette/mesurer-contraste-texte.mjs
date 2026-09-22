/**
 * Mesure bornée, sérialisable par Playwright page.evaluate().
 * Couvre le texte DOM sur une pile de fonds unis RGB(A), dont un fond opaque.
 * Les rendus non modélisés sont indéterminés, jamais réputés conformes.
 * Ne remplace pas une inspection : pas d'analyse exhaustive des recouvrements,
 * de l'anticrénelage, des SVG, des médias, ni des géométries complexes.
 */
export function mesurerContrasteTexte({ selector = 'body' } = {}) {
  const root = document.querySelector(selector);
  if (!root) throw new Error(`Périmètre de contraste absent : ${selector}`);
  const parse = value => {
    const match = value.match(/^rgba?\(\s*([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)(?:\s*[,/]\s*([\d.]+))?\s*\)$/);
    if (!match) return null;
    const color = [Number(match[1]), Number(match[2]), Number(match[3]), match[4] === undefined ? 1 : Number(match[4])];
    return color.slice(0, 3).every(channel => channel >= 0 && channel <= 255) && color[3] >= 0 && color[3] <= 1 ? color : null;
  };
  const luminance = rgb => rgb.slice(0, 3).map(channel => channel / 255)
    .map(channel => channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4)
    .reduce((sum, channel, index) => sum + channel * [.2126, .7152, .0722][index], 0);
  const over = (foreground, background) => foreground.slice(0, 3)
    .map((channel, index) => channel * foreground[3] + background[index] * (1 - foreground[3]));
  const pseudoPresent = (element, pseudo) => {
    const style = getComputedStyle(element, pseudo);
    return style.content !== 'none' && style.content !== 'normal'
      && style.display !== 'none' && style.visibility !== 'hidden';
  };
  const results = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const text = node.textContent.trim();
    const element = node.parentElement;
    if (!text || !element || element.closest('script,style,noscript,template')) continue;
    const style = getComputedStyle(element);
    if (style.visibility !== 'visible') continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const rectangles = [...range.getClientRects()].filter(rectangle => rectangle.width > 0 && rectangle.height > 0);
    if (!rectangles.length) continue;

    const reasons = new Set();
    const layers = [];
    let opaqueBackground = false;
    if (!(element instanceof HTMLElement)) reasons.add('texte-non-html');
    const foreground = parse(style.webkitTextFillColor || style.color);
    if (!foreground) reasons.add('couleur-texte-non-rgb');
    for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
      const current = getComputedStyle(ancestor);
      if (Number(current.opacity) !== 1) reasons.add('opacite-de-groupe');
      if (current.backgroundImage !== 'none') reasons.add('image-ou-degrade');
      if (current.filter !== 'none' || (current.backdropFilter && current.backdropFilter !== 'none')) reasons.add('filtre');
      if (current.mixBlendMode !== 'normal' || current.backgroundBlendMode !== 'normal') reasons.add('mode-de-fusion');
      if (current.maskImage && current.maskImage !== 'none') reasons.add('masque');
      if (current.clipPath && current.clipPath !== 'none') reasons.add('decoupe');
      if (current.backgroundClip === 'text') reasons.add('fond-dans-le-texte');
      if (current.textShadow !== 'none') reasons.add('ombre-de-texte');
      if (current.boxShadow.includes('inset')) reasons.add('ombre-interieure');
      if (pseudoPresent(ancestor, '::before') || pseudoPresent(ancestor, '::after')) reasons.add('pseudo-element');
      // Une animation peut changer la couleur ou l'opacité après l'échantillon.
      if (ancestor.getAnimations().some(animation => animation.playState === 'running')) reasons.add('animation-en-cours');
      if (opaqueBackground) continue;
      const background = parse(current.backgroundColor);
      if (!background) {
        reasons.add('couleur-fond-non-rgb');
        continue;
      }
      if (background[3] === 0) continue;
      const box = ancestor.getBoundingClientRect();
      if (rectangles.some(rectangle => rectangle.left < box.left - 1 || rectangle.right > box.right + 1
        || rectangle.top < box.top - 1 || rectangle.bottom > box.bottom + 1)) reasons.add('fond-hors-zone-texte');
      layers.push(background);
      opaqueBackground = background[3] === 1;
    }
    if (!opaqueBackground) reasons.add('fond-opaque-non-determine');
    const base = { texte: text.slice(0, 100), color: style.color, px: Number.parseFloat(style.fontSize) };
    if (reasons.size > 0) {
      results.push({ ...base, statut: 'indetermine', raisons: [...reasons], ratio: null });
      continue;
    }
    let background = layers.at(-1).slice(0, 3);
    for (let index = layers.length - 2; index >= 0; index--) background = over(layers[index], background);
    const renderedForeground = over(foreground, background);
    const light = luminance(renderedForeground);
    const dark = luminance(background);
    const ratio = (Math.max(light, dark) + .05) / (Math.min(light, dark) + .05);
    const large = base.px >= 24 || (base.px >= 18.66 && Number.parseInt(style.fontWeight) >= 700);
    const threshold = large ? 3 : 4.5;
    results.push({ ...base, statut: ratio >= threshold ? 'conforme' : 'sous-seuil', ratio,
      seuil: threshold, fondCompose: background, texteCompose: renderedForeground });
  }
  const failures = results.filter(result => result.statut === 'sous-seuil');
  const unknown = results.filter(result => result.statut === 'indetermine');
  return {
    perimetre: selector,
    portee: 'Texte DOM sur fonds unis RGB(A), sans effets ni recouvrements complexes. Inspection visuelle complémentaire nécessaire.',
    total: results.length,
    conformes: results.filter(result => result.statut === 'conforme').length,
    sousAA: failures.length,
    indetermines: unknown.length,
    verdict: failures.length ? 'sous-seuil' : unknown.length || !results.length ? 'indetermine' : 'conforme-dans-le-perimetre',
    exemples: failures.slice(0, 25),
    inconnus: unknown.slice(0, 25),
    resultats: results,
  };
}
