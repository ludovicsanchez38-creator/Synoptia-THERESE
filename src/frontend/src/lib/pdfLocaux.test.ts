import { expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';

const h = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock('@tauri-apps/api/core', () => ({ invoke: h.invoke }));
vi.mock('../services/api/core', () => ({ getSessionToken: () => 'jeton-factice', initializeAuth: vi.fn().mockResolvedValue(undefined) }));
import { ouvrirPdfFacture } from './pdfLocaux';

it('le PDF 0.83 ne fait plus partie des ressources du guide embarqué', () => {
  for (const nom of ['tauri.conf.json', 'tauri.linux.conf.json']) {
    const conf = JSON.parse(readFileSync(`src-tauri/${nom}`, 'utf8'));
    expect(Object.values(conf.bundle.resources)).not.toContain('resources/guide-therese-0.83.pdf');
  }
  const acl = JSON.parse(readFileSync('src-tauri/capabilities/default.json', 'utf8'));
  expect(acl.permissions).not.toContainEqual(expect.objectContaining({ identifier: 'opener:allow-open-path' }));
});

it('le guide embarqué référence quatre captures présentes dans sa source', () => {
  const racine = '../../docs/';
  const source = readFileSync(`${racine}USER_GUIDE_ALPHA.md`, 'utf8');
  expect(source).toMatch(/^# Guide des testeurs de THÉRÈSE 0\.85$/m);
  const captures = [...source.matchAll(/!\[[^\]]+\]\((guide-0\.85\/[^)]+)\)/g)];
  expect(captures).toHaveLength(4);
  for (const [, capture] of captures) {
    expect(readFileSync(racine + capture).subarray(1, 4).toString()).toBe('PNG');
  }
});

it('demande au moteur le seul PDF de cette facture, sans chemin fourni par l’écran', async () => {
  await ouvrirPdfFacture('inv-1');
  expect(h.invoke).toHaveBeenCalledWith('ouvrir_pdf_facture', { invoiceId: 'inv-1', token: 'jeton-factice' });
});
