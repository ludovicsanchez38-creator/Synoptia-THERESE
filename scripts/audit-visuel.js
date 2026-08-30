/**
 * Audit visuel de THÉRÈSE dans l'application LANCÉE.
 *
 * À coller dans la console de la fenêtre de développement (port 1420), puis :
 *   await window.__balayer(window.__SURFACES); window.__rapport();
 *
 * Pourquoi cet outil existe : les tests statiques lisent des className. Ils ne
 * voient ni les couleurs posées en style inline, ni ce qui est composé au
 * rendu. Le 30/08/2026 ils déclaraient l'application propre alors que les cinq
 * conseillers du Board s'affichaient à 1,81:1.
 *
 * Deux pièges, tombés dedans avant de les écrire ici :
 *
 * 1. NE PAS calculer la luminance en parsant la chaîne de couleur. Les fonds
 *    de cette application sont parfois en `oklab(...)` : un parseur naïf lit
 *    « 0.999994 » comme un canal rouge et annonce du noir. Cinquante faux
 *    positifs sur le panneau des raccourcis. Ici c'est le navigateur qui
 *    convertit, via un canvas 1x1 : il gère oklab, lch, color(), et compose
 *    correctement l'alpha.
 *
 * 2. NE PAS mesurer pendant une bascule de thème, et surtout PAS avec l'onglet
 *    en arrière-plan. Le navigateur gèle les transitions d'un document
 *    `hidden` : le fond du body reste indéfiniment celui du thème de départ
 *    pendant que --color-bg est déjà celui d'arrivée. J'ai lu onze faux
 *    défauts comme ça, puis failli conclure que le body ne suivait pas le
 *    thème. Appeler window.__sansTransition() AVANT de basculer, et vérifier
 *    que getComputedStyle(document.body).backgroundColor vaut bien la valeur
 *    attendue avant de mesurer quoi que ce soit.
 */

/** Coupe transitions et animations : sans ça, une mesure dans un onglet en
 *  arrière-plan lit un état figé au milieu du fondu entre deux thèmes. */
window.__sansTransition = function () {
  if (document.getElementById('__sans-transition')) return;
  const st = document.createElement('style');
  st.id = '__sans-transition';
  st.textContent = '*,*::before,*::after{transition:none !important;animation:none !important;}';
  document.head.appendChild(st);
};

const cv = document.createElement('canvas');
cv.width = cv.height = 1;
const ctx = cv.getContext('2d', { willReadFrequently: true });

/** Résout et compose une pile de couleurs CSS en RGB, via le moteur du navigateur. */
window.__rgb = function (couleurs, base) {
  ctx.clearRect(0, 0, 1, 1);
  ctx.fillStyle = base || '#FFFFFF';
  ctx.fillRect(0, 0, 1, 1);
  for (const c of couleurs) {
    try { ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1); } catch (e) { /* couleur invalide : ignorée */ }
  }
  const d = ctx.getImageData(0, 0, 1, 1).data;
  return [d[0], d[1], d[2]];
};

window.__lum = function (rgb) {
  const v = rgb.map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
  return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
};

window.__audit = function () {
  const base = window.__rgb([
    getComputedStyle(document.documentElement).backgroundColor,
    getComputedStyle(document.body).backgroundColor,
  ]);
  const baseHex = `rgb(${base.join(',')})`;
  const pileFond = (el) => {
    const p = [];
    let e = el;
    while (e && e !== document.documentElement) { p.push(getComputedStyle(e).backgroundColor); e = e.parentElement; }
    return window.__rgb(p.reverse(), baseHex);
  };
  const rap = (a, b) => { const [h, l] = [window.__lum(a), window.__lum(b)].sort((x, y) => y - x); return (h + 0.05) / (l + 0.05); };
  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity < 0.5) return false;
    const r = el.getBoundingClientRect();
    return r.width > 2 && r.height > 2;
  };

  const contraste = [], rayons = {}, tailles = {}, polices = {}, clics = [], cibles = [];
  for (const el of document.querySelectorAll('*')) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    const t = [...el.childNodes].filter((n) => n.nodeType === 3 && n.textContent.trim())
      .map((n) => n.textContent.trim()).join('');
    if (t) {
      const px = parseFloat(s.fontSize);
      const gras = +s.fontWeight >= 700;
      const seuil = px >= 24 || (px >= 18.66 && gras) ? 3 : 4.5;
      const f = pileFond(el);
      const c = window.__rgb([s.color], `rgb(${f.join(',')})`);
      const r = rap(c, f);
      if (r < seuil) {
        contraste.push({ texte: t.slice(0, 30), ratio: +r.toFixed(2), px, couleur: `rgb(${c.join(',')})`, fond: `rgb(${f.join(',')})`, brut: s.color });
      }
      tailles[px] = (tailles[px] || 0) + 1;
      const fam = s.fontFamily.split(',')[0].replace(/"/g, '');
      polices[fam] = (polices[fam] || 0) + 1;
    }
    const br = s.borderRadius;
    if (br && br !== '0px') rayons[br] = (rayons[br] || 0) + 1;
    if (el.matches('button, a[href], [role="button"], [role="tab"], input, select, textarea')) {
      const px = parseFloat(s.fontSize);
      const propre = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (propre && px < 14) clics.push({ t: (el.textContent || '').trim().slice(0, 24), px });
      const r = el.getBoundingClientRect();
      if (Math.min(r.width, r.height) < 24) {
        cibles.push({ t: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 22), w: Math.round(r.width), h: Math.round(r.height) });
      }
    }
  }
  const tri = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]);
  return {
    sousAA: contraste.length, contraste: contraste.slice(0, 8),
    rayons: tri(rayons), tailles: tri(tailles), polices: tri(polices),
    clicsSous14: clics.length, exClics: clics.slice(0, 5),
    ciblesSous24: cibles.length, exCibles: cibles.slice(0, 6),
    noeuds: document.querySelectorAll('*').length,
  };
};

window.__SURFACES = [
  'home.open', 'crm.open', 'email.open', 'calendar.open', 'tasks.open',
  'invoices.open', 'projects.open', 'files.open', 'documents.open', 'memory.open',
  'board.open', 'actions.open', 'settings.open', 'shortcuts.open',
  'prompt-library.open', 'guided.open', 'conversations.toggle',
];

window.__res = window.__res || {};
window.__balayer = async function (cibles) {
  const dodo = (ms) => new Promise((r) => setTimeout(r, ms));
  for (const id of cibles) {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await dodo(150);
    try { window.__therese.runAction(id); } catch (e) { window.__res[id] = { erreur: String(e).slice(0, 80) }; continue; }
    await dodo(1100);
    window.__res[id] = window.__audit();
  }
  return Object.keys(window.__res).length;
};

window.__rapport = function () {
  return Object.fromEntries(Object.entries(window.__res).map(([k, v]) => [
    k, v.erreur || `AA:${v.sousAA} clics<14:${v.clicsSous14} cibles<24:${v.ciblesSous24} rayons:${v.rayons.map((r) => r[0]).join('/')} tailles:${v.tailles.map((t) => t[0]).join('/')}`,
  ]));
};
