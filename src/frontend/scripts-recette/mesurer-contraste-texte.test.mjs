// node scripts-recette/mesurer-contraste-texte.test.mjs
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { mesurerContrasteTexte } from './mesurer-contraste-texte.mjs';

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const results = [];
  const measure = async (name, css, markup = '<div id="case">Texte témoin</div>') => {
    await page.setContent(`<!doctype html><style>
      html, body { margin: 0; background: black; }
      #case { padding: 20px; font: 16px sans-serif; color: white; }
      ${css}
    </style>${markup}`);
    const result = await page.evaluate(mesurerContrasteTexte, { selector: '#case' });
    results.push({ name, result });
    assert.equal(result.total, 1, name);
    return result;
  };

  const green = await measure('vert réel : blanc sur noir', '');
  assert.equal(green.verdict, 'conforme-dans-le-perimetre');
  assert.equal(green.resultats[0].ratio, 21);

  const red = await measure('rouge réel : gris sur gris', '#case { color: rgb(119,119,119); background: rgb(128,128,128); }');
  assert.equal(red.sousAA, 1);
  assert.ok(Math.abs(red.resultats[0].ratio - 1.1338543825550624) < .000001);

  const alpha = await measure('B-936 : blanc alpha .5 sur noir', '#case { color: rgb(119,119,119); background: rgba(255,255,255,.5); }');
  assert.equal(alpha.sousAA, 1);
  assert.deepEqual(alpha.resultats[0].fondCompose, [127.5, 127.5, 127.5]);
  assert.ok(Math.abs(alpha.resultats[0].ratio - 1.126095091908557) < .000001);

  const nested = await measure('plusieurs couches alpha', '#case { background: rgba(255,255,255,.5); } #layer { padding: 20px; background: rgba(255,255,255,.5); }', '<div id="layer"><div id="case">Texte témoin</div></div>');
  assert.deepEqual(nested.resultats[0].fondCompose, [191.25, 191.25, 191.25]);

  const translucentText = await measure('texte alpha sur fond opaque', '#case { color: rgba(255,255,255,.5); }');
  assert.deepEqual(translucentText.resultats[0].texteCompose, [127.5, 127.5, 127.5]);

  for (const [name, css, reason] of [
    ['dégradé', '#case { background: linear-gradient(white, black); }', 'image-ou-degrade'],
    ['image', '#case { background-image: url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27/%3E"); }', 'image-ou-degrade'],
    ['opacité du groupe', 'body { opacity: .5; }', 'opacite-de-groupe'],
    ['pseudo-élément', '#case::before { content: ""; position: absolute; inset: 0; background: white; }', 'pseudo-element'],
    ['filtre', '#case { filter: invert(1); }', 'filtre'],
    ['couleur non prise en charge', '#case { color: oklch(.8 .1 100); }', 'couleur-texte-non-rgb'],
    ['aucun fond opaque connu', 'html, body { background: transparent; }', 'fond-opaque-non-determine'],
  ]) {
    const unknown = await measure(name, css);
    assert.equal(unknown.verdict, 'indetermine', name);
    assert.equal(unknown.conformes, 0, name);
    assert.equal(unknown.resultats[0].ratio, null, name);
    assert.ok(unknown.resultats[0].raisons.includes(reason), name);
  }

  await page.setContent('<style>body { background: black; color: white; }</style><div id="case" hidden>Texte caché</div>');
  const empty = await page.evaluate(mesurerContrasteTexte, { selector: '#case' });
  assert.equal(empty.total, 0);
  assert.equal(empty.verdict, 'indetermine');
  console.log(JSON.stringify({ passed: true, browser: browser.version(), fixtures: results, empty }, null, 2));
} finally {
  await browser.close();
}
