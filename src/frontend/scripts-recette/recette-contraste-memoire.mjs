// P-002 (lot 0.74) : mesure du contraste des textes de la vue Mémoire sur la pile jetable (Vite 1420 + moteur 17393, contacts présents). Résultat attendu : sousAA = 0 en clair et en sombre.
import { chromium } from 'playwright';
const FRONT = 'http://127.0.0.1:1420';
const b = await chromium.launch({ headless: true });
const res = {};
for (const theme of ['light', 'dark']) {
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: theme });
  const p = await ctx.newPage();
  await p.goto(`${FRONT}/?prototype=conversation-canvas&scenario=today`, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1500);
  await p.evaluate(() => window.__therese.runAction('memory.open'));
  await p.getByTestId('memory-panel').waitFor();
  await p.waitForTimeout(2000);
  res[theme] = await p.evaluate(() => {
    const lum = (r, g, b) => { const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const parse = (s) => { const m = s && s.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/); return m ? [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]] : null; };
    const fond = (el) => { let e = el; while (e) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c[3] > 0.99) return c; e = e.parentElement; } return [255, 255, 255, 1]; };
    const out = []; let total = 0;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      const t = n.textContent.trim(); if (!t) continue; const el = n.parentElement; if (!el) continue;
      const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
      const fg = parse(cs.color); if (!fg) continue;
      const bg = fond(el);
      const a = fg[3]; const mix = fg.map((c, i) => i < 3 ? Math.round(c * a + bg[i] * (1 - a)) : 1);
      const L1 = lum(...mix.slice(0, 3)), L2 = lum(...bg.slice(0, 3));
      const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
      const px = parseFloat(cs.fontSize); const gras = parseInt(cs.fontWeight) >= 700;
      const grand = px >= 24 || (px >= 18.66 && gras); const seuil = grand ? 3 : 4.5;
      total++;
      if (ratio < seuil) out.push({ texte: t.slice(0, 40), ratio: +ratio.toFixed(2), px, color: cs.color, bg: `rgb(${bg.slice(0, 3).join(',')})`, cls: (el.className || '').toString().slice(0, 60) });
    }
    const textes = []; const w2 = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let m; while ((m = w2.nextNode())) { const t = m.textContent.trim(); if (t) textes.push(t.slice(0, 30)); }
    return { total, sousAA: out.length, exemples: out.slice(0, 25), textes: textes.slice(0, 60) };
  });
  await ctx.close();
}
await b.close();
console.log(JSON.stringify(res, null, 1));
