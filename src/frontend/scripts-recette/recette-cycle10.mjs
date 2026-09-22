/** Cycle 10 : UI réelle, données synthétiques aux frontières HTTP, aucune écriture autorisée. */
import { chromium, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const sortie = new URL('../../../.app-loop/cycles/10/recette/', import.meta.url);
await mkdir(sortie, { recursive: true });
const date = '2026-09-22T10:00:00Z';
const contact = { id: 'contact-c10', first_name: 'Victor', last_name: 'Ruiz', company: 'Entreprise Ardent', email: 'victor@example.invalid', phone: null, address: null, notes: null, tags: [], stage: 'contact', scope: 'global', score: 0, created_at: date, updated_at: date };
const projet = { id: 'projet-c10', name: 'Chantier Ardent c10', description: 'Projet pour Victor Ruiz', contact_id: contact.id, status: 'active', budget: 1200, notes: 'Relancer Entreprise Ardent', tags: ['Ruiz'], created_at: date, updated_at: date };
const fichier = { id: 'fichier-c10', name: 'Devis Victor Ruiz.pdf', path: '/Dossiers/Victor Ruiz/devis.pdf', extension: '.pdf', size: 400, mime_type: 'application/pdf', chunk_count: 1, created_at: date };
const facture = { id: 'facture-c10', invoice_number: 'FAC-C10-001', document_type: 'facture', contact_id: contact.id, contact_name: 'Victor Ruiz', tva_applicable: true, currency: 'EUR', issue_date: date, due_date: date, status: 'draft', subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, lines: [], created_at: date, updated_at: date };
const resultats = [];
const navigateur = await chromium.launch({ headless: true });
try {
  for (const theme of ['light', 'dark']) {
    const contexte = await navigateur.newContext({ viewport: { width: 1280, height: 800 }, locale: 'fr-FR', colorScheme: theme, reducedMotion: 'reduce' });
    const page = await contexte.newPage();
    const erreurs = [], mutations = [], reseau = [];
    let panneSync = true;
    page.on('pageerror', (error) => erreurs.push(error.message));
    page.on('response', (response) => { if (response.status() >= 400) reseau.push({ url: response.url(), status: response.status() }); });
    await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
      const requete = route.request(), url = new URL(requete.url()), chemin = url.pathname;
      if (url.port === '17293') throw new Error('Le moteur réel est hors périmètre');
      if (!['GET', 'OPTIONS'].includes(requete.method())) {
        mutations.push({ chemin, methode: requete.method() });
        return route.fulfill({ status: 403, json: { detail: 'Recette en lecture seule' } });
      }
      if (chemin === '/api/config/onboarding-complete') return route.fulfill({ json: { completed: true } });
      if (chemin === '/api/memory/projects') return route.fulfill({ json: [projet] });
      if (chemin === '/api/memory/contacts') return route.fulfill({ json: [contact] });
      if (chemin === `/api/memory/projects/${projet.id}/files`) return route.fulfill({ json: { files: [fichier], total: 1, truncated: false } });
      if (chemin === `/api/projects/${projet.id}/sync`) return route.fulfill({ status: panneSync ? 503 : 200, json: panneSync ? { detail: 'Panne témoin C10' } : { racine: '/Dossiers/Victor Ruiz/Chantier Ardent c10', generation: 1, dernier_plan: null } });
      if (chemin === '/api/invoices') return route.fulfill({ json: [facture] });
      return route.continue();
    });
    await page.goto('http://127.0.0.1:1420', { waitUntil: 'networkidle' });
    expect(await page.evaluate(() => document.visibilityState === 'visible' && document.timeline.currentTime > 0)).toBe(true);
    await page.evaluate((valeur) => document.documentElement.setAttribute('data-theme', valeur), theme);
    const action = (id) => page.evaluate((identifiant) => window.__therese.runAction(identifiant), id);
    const capture = async (nom) => {
      // isVisible ne garantit pas que le fondu Framer Motion est terminé.
      await page.waitForFunction(() => [...document.querySelectorAll('[role=dialog]')].every((dialogue) => {
        for (let element = dialogue; element; element = element.parentElement) {
          if (Number(getComputedStyle(element).opacity) < .99) return false;
        }
        return true;
      }));
      await page.screenshot({ path: fileURLToPath(new URL(`${theme}-${nom}.png`, sortie)) });
    };
    await action('projects.open');
    await page.getByText(projet.name, { exact: true }).click();
    let dialogue = page.getByRole('dialog', { name: 'Modifier le projet', exact: true });
    await expect(dialogue.getByRole('alert').filter({ hasText: /charg|Panne|impossible/i })).toBeVisible();
    await expect(dialogue.getByRole('button', { name: 'Attacher', exact: true })).toHaveCount(0);
    await dialogue.getByRole('alert').scrollIntoViewIfNeeded();
    await capture('sync-erreur');
    panneSync = false;
    await dialogue.getByRole('button', { name: /Réessayer/ }).click();
    await expect(dialogue.getByText('/Dossiers/Victor Ruiz/Chantier Ardent c10', { exact: true })).toBeVisible();
    await page.evaluate(async ({ contact, projet }) => {
      const { useDemoStore } = await import('/src/stores/demoStore.ts');
      const { buildReplacementMap } = await import('/src/lib/demoMask.ts');
      useDemoStore.setState({ enabled: true, replacementMap: buildReplacementMap([contact], [projet]) });
    }, { contact, projet });
    dialogue = page.getByRole('dialog', { name: 'Consulter le projet', exact: true });
    await expect(dialogue.getByText(/Désactive le mode démo/).first()).toBeVisible();
    await expect(dialogue.getByRole('textbox', { name: /Nom du projet/ })).not.toHaveValue(projet.name);
    await expect(dialogue.getByRole('button', { name: 'Mettre à jour', exact: true })).toBeDisabled();
    expect(await dialogue.evaluate((element) => `${element.textContent} ${[...element.querySelectorAll('input,textarea')].map((champ) => champ.value).join(' ')}`)).not.toMatch(/Victor|Ruiz|Entreprise Ardent|Chantier Ardent c10/);
    await capture('projet-demo');
    await dialogue.getByText('Mode démo : lecture seule', { exact: true }).scrollIntoViewIfNeeded();
    await capture('projet-demo-haut');
    await dialogue.getByRole('button', { name: 'Fermer', exact: true }).click();
    await page.evaluate(async () => { const { useDemoStore } = await import('/src/stores/demoStore.ts'); useDemoStore.setState({ enabled: false }); });
    await action('invoices.open');
    const suppressionFacture = page.getByTitle('Supprimer', { exact: true });
    await suppressionFacture.focus();
    await suppressionFacture.click();
    dialogue = page.getByRole('dialog', { name: 'Confirmer la suppression', exact: true });
    await expect(dialogue.getByRole('button', { name: 'Annuler', exact: true })).toBeFocused();
    await page.keyboard.press('Shift+Tab');
    await expect(dialogue.getByRole('button', { name: 'Supprimer', exact: true })).toBeFocused();
    await capture('facture-focus');
    await page.keyboard.press('Escape');
    await expect(suppressionFacture).toBeFocused();
    await action('memory.open');
    const parcours = [
      { bouton: 'Supprimer Victor Ruiz', titre: 'Supprimer le contact ?' },
      { bouton: 'Actions RGPD', menu: 'Exporter (Art. 20)', titre: 'Export RGPD' },
      { bouton: 'Actions RGPD', menu: 'Anonymiser (Art. 17)', titre: 'Anonymisation RGPD' },
      { bouton: 'Actions RGPD', menu: 'Renouveler consentement', titre: 'Renouveler le consentement' },
    ];
    for (const [index, cas] of parcours.entries()) {
      const origine = page.getByRole('button', { name: cas.bouton, exact: true });
      await origine.focus();
      await origine.click();
      if (cas.menu) await page.getByRole('button', { name: cas.menu, exact: true }).click();
      dialogue = page.getByRole('dialog', { name: cas.titre, exact: true });
      await expect(dialogue).toBeVisible();
      expect(await dialogue.evaluate((element) => element.contains(document.activeElement))).toBe(true);
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Shift+Tab');
        expect(await dialogue.evaluate((element) => element.contains(document.activeElement))).toBe(true);
      }
      await capture(`contacts-${index}`);
      await dialogue.getByRole('button', { name: 'Annuler', exact: true }).click();
      await expect(dialogue).toBeHidden();
      await expect(origine).toBeFocused();
    }
    expect(mutations).toEqual([]);
    expect(erreurs).toEqual([]);
    expect(reseau.filter((item) => !item.url.endsWith(`/api/projects/${projet.id}/sync`) || item.status !== 503)).toEqual([]);
    resultats.push({ theme, viewport: '1280x800', controles: ['sync-erreur-reessai', 'demo-lecture-seule', 'facture-focus', 'contacts-suppression', 'rgpd-export', 'rgpd-anonymisation', 'rgpd-renouvellement'], erreurs, mutations, reseau });
    await contexte.close();
  }
} finally {
  await navigateur.close();
  await writeFile(new URL('resultats.json', sortie), `${JSON.stringify(resultats, null, 2)}\n`);
}
console.log(JSON.stringify({ themes: resultats.length, ok: resultats.length === 2 }));
