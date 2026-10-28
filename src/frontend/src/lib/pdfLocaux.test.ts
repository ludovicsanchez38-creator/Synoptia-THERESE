import { expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
const h = vi.hoisted(() => ({ openPath: vi.fn(), invoke: vi.fn(), resolveResource: vi.fn().mockResolvedValue('/bundle/resources/guide-therese-0.82.pdf') }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath: h.openPath }));
vi.mock('@tauri-apps/api/path', () => ({ resolveResource: h.resolveResource }));
vi.mock('@tauri-apps/api/core', () => ({ invoke: h.invoke }));
vi.mock('../services/api/core', () => ({ getSessionToken: () => 'jeton-factice', initializeAuth: vi.fn().mockResolvedValue(undefined) }));
import { ouvrirGuide, ouvrirPdfFacture, GUIDE_RESSOURCE } from './pdfLocaux';
it('résout la ressource du bundle et l’ouvre avec le greffon de fichiers', async () => {
  await ouvrirGuide();
  expect(h.resolveResource).toHaveBeenCalledWith(GUIDE_RESSOURCE);
  expect(h.openPath).toHaveBeenCalledWith('/bundle/resources/guide-therese-0.82.pdf');
  const conf = JSON.parse(readFileSync('src-tauri/tauri.conf.json', 'utf8'));
  expect(conf.bundle.resources).toContain(GUIDE_RESSOURCE);
  const linux = JSON.parse(readFileSync('src-tauri/tauri.linux.conf.json', 'utf8'));
  expect(linux.bundle.resources).toContain(GUIDE_RESSOURCE);
  const acl = JSON.parse(readFileSync('src-tauri/capabilities/default.json', 'utf8'));
  expect(acl.permissions.find((p: { identifier?: string }) => p.identifier === 'opener:allow-open-path').allow)
    .toEqual([{ path: '$RESOURCE/' + GUIDE_RESSOURCE }]);
});
it('demande au moteur le seul PDF de cette facture, sans chemin fourni par l’écran', async () => {
  await ouvrirPdfFacture('inv-1');
  expect(h.invoke).toHaveBeenCalledWith('ouvrir_pdf_facture', { invoiceId: 'inv-1', token: 'jeton-factice' });
});
