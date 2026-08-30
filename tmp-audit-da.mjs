import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const TOKEN = '-Y2asnKQC-Zs4PHQ5VcXo8-h051b_0rfwbz9CJPmuMA';
const OUT = '/tmp/therese-audit-da';
mkdirSync(OUT, { recursive: true });

const CONTRAST_HELPER = `
(() => {
  function clamp01(n) { return Math.min(1, Math.max(0, n)); }
  function srgbTransfer(c) {
    return c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1/2.4) - 0.055;
  }
  function srgbToLin(c) {
    const x = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    return x;
  }
  function oklabToSrgb(L, a, b) {
    const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
    const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
    const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
    const l = l_ * l_ * l_;
    const m = m_ * m_ * m_;
    const s = s_ * s_ * s_;
    let r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
    let g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
    let bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;
    return [srgbTransfer(r), srgbTransfer(g), srgbTransfer(bl)].map(clamp01);
  }
  function parseColor(str) {
    if (!str || str === 'transparent' || str === 'none') return { r:0,g:0,b:0,a:0, raw: str };
    str = String(str).trim();
    let m = str.match(/^rgba?\\(([^)]+)\\)$/i);
    if (m) {
      const p = m[1].split(/[,\\s\\/]+/).filter(Boolean);
      const r = p[0].includes('%') ? parseFloat(p[0])/100 : parseFloat(p[0])/255;
      const g = p[1].includes('%') ? parseFloat(p[1])/100 : parseFloat(p[1])/255;
      const b = p[2].includes('%') ? parseFloat(p[2])/100 : parseFloat(p[2])/255;
      const a = p[3] == null ? 1 : parseFloat(p[3]);
      return { r, g, b, a, raw: str };
    }
    m = str.match(/^oklab\\(([^)]+)\\)$/i);
    if (m) {
      const inner = m[1].replace('/', ' ');
      const p = inner.trim().split(/[\\s,]+/).filter(Boolean);
      let L = parseFloat(p[0]);
      if (p[0].includes('%')) L = L / 100;
      const a = parseFloat(p[1]);
      const b = parseFloat(p[2]);
      const alpha = p[3] == null ? 1 : parseFloat(p[3]);
      const [r,g,bl] = oklabToSrgb(L, a, b);
      return { r, g, b: bl, a: alpha, raw: str };
    }
    m = str.match(/^oklch\\(([^)]+)\\)$/i);
    if (m) {
      const inner = m[1].replace('/', ' ');
      const p = inner.trim().split(/[\\s,]+/).filter(Boolean);
      let L = parseFloat(p[0]);
      if (p[0].includes('%')) L = L / 100;
      const C = parseFloat(p[1]);
      let h = parseFloat(p[2]);
      if (String(p[2]).toLowerCase().includes('deg') || !Number.isNaN(h)) {
        const hr = (h * Math.PI) / 180;
        const a = C * Math.cos(hr);
        const b = C * Math.sin(hr);
        const alpha = p[3] == null ? 1 : parseFloat(p[3]);
        const [r,g,bl] = oklabToSrgb(L, a, b);
        return { r, g, b: bl, a: alpha, raw: str };
      }
    }
    m = str.match(/^color\\(srgb\\s+([^)]+)\\)$/i);
    if (m) {
      const p = m[1].replace('/', ' ').trim().split(/\\s+/);
      return { r: parseFloat(p[0]), g: parseFloat(p[1]), b: parseFloat(p[2]), a: p[3]==null?1:parseFloat(p[3]), raw: str };
    }
    m = str.match(/^#([0-9a-f]{3,8})$/i);
    if (m) {
      let h = m[1];
      if (h.length === 3) h = h.split('').map(c=>c+c).join('');
      const r = parseInt(h.slice(0,2),16)/255;
      const g = parseInt(h.slice(2,4),16)/255;
      const b = parseInt(h.slice(4,6),16)/255;
      const a = h.length >= 8 ? parseInt(h.slice(6,8),16)/255 : 1;
      return { r, g, b, a, raw: str };
    }
    // last resort: let the browser resolve via canvas... skip
    return { r:0,g:0,b:0,a:0, raw: str, unparsed: true };
  }
  function composite(fg, bg) {
    const a = clamp01(fg.a);
    return {
      r: fg.r * a + bg.r * (1-a),
      g: fg.g * a + bg.g * (1-a),
      b: fg.b * a + bg.b * (1-a),
      a: 1
    };
  }
  function relLum(c) {
    const R = srgbToLin(clamp01(c.r));
    const G = srgbToLin(clamp01(c.g));
    const B = srgbToLin(clamp01(c.b));
    return 0.2126*R + 0.7152*G + 0.0722*B;
  }
  function contrast(c1, c2) {
    const L1 = relLum(c1), L2 = relLum(c2);
    const hi = Math.max(L1,L2), lo = Math.min(L1,L2);
    return (hi + 0.05) / (lo + 0.05);
  }
  function hex(c) {
    const n = (x) => Math.round(clamp01(x)*255).toString(16).padStart(2,'0');
    return '#' + n(c.r)+n(c.g)+n(c.b);
  }
  function bgOf(el) {
    let acc = { r:1, g:1, b:1, a:0 };
    const stack = [];
    let node = el;
    while (node && node !== document.documentElement) {
      const cs = getComputedStyle(node);
      stack.push(parseColor(cs.backgroundColor));
      node = node.parentElement;
    }
    const htmlBg = parseColor(getComputedStyle(document.documentElement).backgroundColor);
    const bodyBg = parseColor(getComputedStyle(document.body).backgroundColor);
    stack.push(bodyBg, htmlBg);
    // compose from farthest to nearest
    let out = { r: 0.95, g: 0.96, b: 0.99, a: 1 }; // fallback paper
    const theme = document.documentElement.getAttribute('data-theme');
    if (theme === 'dark') out = { r: 11/255, g: 18/255, b: 38/255, a: 1 };
    for (let i = stack.length - 1; i >= 0; i--) {
      const layer = stack[i];
      if (!layer || layer.unparsed) continue;
      if (layer.a <= 0.001) continue;
      out = composite(layer, out);
    }
    return out;
  }
  function isVisible(el) {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    if (r.bottom < 0 || r.right < 0 || r.top > innerHeight || r.left > innerWidth) return false;
    return true;
  }
  function textOf(el) {
    return (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 80);
  }
  const results = [];
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  while (walker.nextNode()) {
    const el = walker.currentNode;
    if (!isVisible(el)) continue;
    const cs = getComputedStyle(el);
    const hasOwnText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasOwnText) continue;
    const color = parseColor(cs.color);
    if (color.unparsed || color.a < 0.15) continue;
    const bg = bgOf(el);
    const fg = color.a < 0.999 ? composite(color, bg) : color;
    const ratio = contrast(fg, bg);
    const fs = parseFloat(cs.fontSize);
    const fw = parseInt(cs.fontWeight, 10) || 400;
    const large = fs >= 18 || (fs >= 14 && fw >= 700);
    const aa = large ? 3 : 4.5;
    const key = cs.color + '|' + hex(bg) + '|' + Math.round(fs) + '|' + textOf(el);
    if (seen.has(key)) continue;
    seen.add(key);
    results.push({
      text: textOf(el),
      tag: el.tagName.toLowerCase(),
      className: String(el.className).slice(0, 120),
      colorRaw: cs.color,
      fg: hex(fg),
      bg: hex(bg),
      ratio: Math.round(ratio * 100) / 100,
      fontSize: fs,
      fontWeight: fw,
      large,
      failAA: ratio < aa,
      failAAA: ratio < (large ? 4.5 : 7),
    });
  }
  return results;
})()
`;

function statsFrom(results) {
  const fails = results.filter(r => r.failAA);
  const worst = [...results].sort((a,b) => a.ratio - b.ratio).slice(0, 25);
  return {
    n: results.length,
    failAA: fails.length,
    fails: fails.slice(0, 40),
    worst,
  };
}

async function shot(page, name) {
  await page.screenshot({ path: join(OUT, name + '.png'), fullPage: false });
}

async function waitApp(page) {
  await page.waitForSelector('[data-testid="conversation-canvas-prototype"], [data-testid="app-main"]', { timeout: 20000 });
  await page.waitForTimeout(800);
}

async function setTheme(page, theme) {
  await page.evaluate((t) => {
    document.documentElement.setAttribute('data-theme', t);
    const roots = document.querySelectorAll('[data-theme]');
    roots.forEach(el => el.setAttribute('data-theme', t));
    try {
      const raw = localStorage.getItem('therese-accessibility');
      if (raw) {
        const parsed = JSON.parse(raw);
        const state = parsed.state || parsed;
        state.theme = t;
        localStorage.setItem('therese-accessibility', JSON.stringify(parsed.state ? parsed : { state }));
      }
    } catch {}
  }, theme);
  await page.waitForTimeout(250);
}

async function clickLabel(page, label) {
  const loc = page.getByLabel(label, { exact: true }).first();
  if (await loc.count()) {
    await loc.click({ timeout: 4000 }).catch(() => {});
    return true;
  }
  const txt = page.getByRole('button', { name: label }).first();
  if (await txt.count()) {
    await txt.click({ timeout: 4000 }).catch(() => {});
    return true;
  }
  return false;
}

async function collect(page, label) {
  const contrast = await page.evaluate(CONTRAST_HELPER);
  const meta = await page.evaluate(() => {
    const root = document.documentElement;
    const cs = getComputedStyle(root);
    const tokens = {};
    for (const k of ['--color-bg','--color-surface','--color-text','--color-text-muted','--color-accent','--color-accent-fill','--color-accent-cyan','--color-accent-magenta','--color-success','--color-warning','--color-error','--color-info']) {
      tokens[k] = cs.getPropertyValue(k).trim();
    }
    const sizes = {};
    const radii = {};
    const buttons = { total: 0, brutal: 0, bgText: 0, accentFill: 0, hand: 0 };
    document.querySelectorAll('button').forEach(b => {
      if (b.offsetParent === null && getComputedStyle(b).display === 'none') return;
      buttons.total++;
      const c = b.className || '';
      if (c.includes('btn-brutal')) buttons.brutal++;
      if (c.includes('bg-text')) buttons.bgText++;
      if (c.includes('bg-accent-fill')) buttons.accentFill++;
      else buttons.hand++;
    });
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
    while (walker.nextNode()) {
      const el = walker.currentNode;
      const st = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (own) {
        const fs = Math.round(parseFloat(st.fontSize));
        sizes[fs] = (sizes[fs] || 0) + 1;
      }
      const rad = st.borderRadius;
      if (rad && rad !== '0px') radii[rad] = (radii[rad] || 0) + 1;
    }
    const heading = document.querySelector('h1, h2')?.innerText?.slice(0, 80) || '';
    return {
      theme: root.getAttribute('data-theme'),
      tokens,
      heading,
      title: document.title,
      sizes,
      radiiTop: Object.entries(radii).sort((a,b)=>b[1]-a[1]).slice(0,12),
      buttons,
      bodyBg: getComputedStyle(document.body).backgroundColor,
      htmlThemeAttr: root.getAttribute('data-theme'),
    };
  });
  return { label, contrast: statsFrom(contrast), meta };
}

const report = { screens: [], notes: [] };

const browser = await chromium.launch({ headless: true, channel: 'chrome' });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 1,
});
await context.addInitScript((token) => {
  window.__THERESE_AUDIT_TOKEN = token;
}, TOKEN);

const page = await context.newPage();
page.on('console', msg => {
  if (msg.type() === 'error') report.notes.push('console:' + msg.text().slice(0, 200));
});

await page.goto('http://localhost:1420/?port=18500', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(1500);

// If splash hangs, try waiting longer
try {
  await waitApp(page);
} catch (e) {
  report.notes.push('waitApp failed: ' + e.message);
  await shot(page, '00-stuck');
}

report.notes.push('url=' + page.url());
report.notes.push('html=' + (await page.content()).slice(0, 400));

// LIGHT home
await setTheme(page, 'light');
await shot(page, '01-accueil-clair');
report.screens.push(await collect(page, 'accueil-clair'));

// Dark home
await setTheme(page, 'dark');
await shot(page, '02-accueil-sombre');
report.screens.push(await collect(page, 'accueil-sombre'));

await setTheme(page, 'light');

// Plus d'outils
await clickLabel(page, "Plus d’outils") || await clickLabel(page, "Plus d'outils");
await page.waitForTimeout(600);
await shot(page, '03-tiroir-clair');
report.screens.push(await collect(page, 'tiroir-clair'));
await setTheme(page, 'dark');
await shot(page, '04-tiroir-sombre');
report.screens.push(await collect(page, 'tiroir-sombre'));
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await setTheme(page, 'light');

// Paramètres
await clickLabel(page, 'Paramètres');
await page.waitForTimeout(700);
await shot(page, '05-parametres-clair');
report.screens.push(await collect(page, 'parametres-clair'));
await setTheme(page, 'dark');
await shot(page, '06-parametres-sombre');
report.screens.push(await collect(page, 'parametres-sombre'));
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await setTheme(page, 'light');

// Projets
await clickLabel(page, 'Projets');
await page.waitForTimeout(800);
await shot(page, '07-projets-clair');
report.screens.push(await collect(page, 'projets-clair'));
await setTheme(page, 'dark');
await shot(page, '08-projets-sombre');
report.screens.push(await collect(page, 'projets-sombre'));
await setTheme(page, 'light');
await clickLabel(page, 'Accueil');
await page.waitForTimeout(400);

// Etabli chips
for (const name of ['Écrire', 'Retrouver', 'Facturer', 'Décider']) {
  const ok = await clickLabel(page, name) || await page.getByRole('button', { name }).first().click().then(()=>true).catch(()=>false);
  await page.waitForTimeout(700);
  const slug = name.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
  await shot(page, `09-${slug}-clair`);
  report.screens.push(await collect(page, slug + '-clair'));
  await setTheme(page, 'dark');
  await shot(page, `10-${slug}-sombre`);
  report.screens.push(await collect(page, slug + '-sombre'));
  await setTheme(page, 'light');
}

// Contacts via retrouver already, try CRM / invoices views via plus d'outils if visible
await clickLabel(page, 'Accueil');
await page.waitForTimeout(300);
await clickLabel(page, "Plus d’outils") || await clickLabel(page, "Plus d'outils");
await page.waitForTimeout(400);
for (const name of ['Pipeline', 'Devis et factures', 'Agenda', 'Contacts', 'Tâches']) {
  const card = page.getByText(name, { exact: true }).first();
  if (await card.count()) {
    await card.click().catch(()=>{});
    await page.waitForTimeout(800);
    const slug = name.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/\\s+/g,'-').toLowerCase();
    await shot(page, `11-${slug}-clair`);
    report.screens.push(await collect(page, slug + '-clair'));
    await setTheme(page, 'dark');
    await shot(page, `12-${slug}-sombre`);
    report.screens.push(await collect(page, slug + '-sombre'));
    await setTheme(page, 'light');
    await clickLabel(page, 'Accueil');
    await page.waitForTimeout(300);
    await clickLabel(page, "Plus d’outils") || await clickLabel(page, "Plus d'outils");
    await page.waitForTimeout(300);
  }
}

writeFileSync(join(OUT, 'report.json'), JSON.stringify(report, null, 2));
console.log('WROTE', join(OUT, 'report.json'));
console.log('screens', report.screens.length);
console.log('notes', report.notes.slice(0, 20));
for (const s of report.screens) {
  console.log(s.label, 'n=', s.contrast.n, 'failAA=', s.contrast.failAA, 'heading=', s.meta.heading, 'theme=', s.meta.theme);
  if (s.contrast.fails.length) {
    for (const f of s.contrast.fails.slice(0, 6)) {
      console.log('  FAIL', f.ratio, f.fg, 'on', f.bg, JSON.stringify(f.text), 'fs='+f.fontSize);
    }
  }
}
await browser.close();
