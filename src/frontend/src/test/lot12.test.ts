/**
 * Lot 12 de la boucle d'amélioration (cycle 3, RP13 + RP14) : gardes de
 * régression sur la source pour les correctifs dont le comportement se
 * vérifie mal en jsdom (sondages, minuteries, Rust, libellés).
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = path.resolve(__dirname, '..');
const lire = (rel: string) => readFileSync(path.join(SRC, rel), 'utf-8');

describe('lot 12 - gardes de régression', () => {
  it('B-441 : le Pipeline partage les consignes de glisser-déposer des autres tableaux', () => {
    const src = lire('components/crm/PipelineView.tsx');
    expect(src).toMatch(/accessibiliteGlisserDeposer\(/);
    expect(src).not.toMatch(/screenReaderInstructions:\s*\{/);
  });

  it('B-442 : en démonstration, le fil des activités masque noms et titres', () => {
    const src = lire('components/crm/CRMPanel.tsx');
    expect(src).toMatch(/annuaire=\{demoEnabled \? allContacts\.map\(/);
    expect(src).toMatch(/maskText\(activity\.title\)/);
  });

  it('B-446 : plus aucune assertion arrière dans le code chargé au démarrage', () => {
    expect(lire('components/chat/ChatInput.tsx')).not.toMatch(/\(\?<[!=]/);
    expect(lire('services/api/variables.ts')).not.toMatch(/\(\?<[!=]/);
  });

  it("B-448 : l'attente du shutdown graceful s'arrête dès que le backend a lâché le port", () => {
    const src = readFileSync(path.resolve(SRC, '..', 'src-tauri/src/lib.rs'), 'utf-8');
    expect(src).toMatch(/fn backend_ecoute_encore/);
    expect(src).not.toMatch(/std::thread::sleep\(std::time::Duration::from_secs\(5\)\)/);
  });

  it('B-451 : aucun identifiant de feuille réel écrit en dur', () => {
    expect(lire('components/settings/CRMSyncPanel.tsx')).not.toMatch(/1gXhiy43/);
  });

  it('B-453 : la purge annonce quand ses réglages ne viennent pas du serveur', () => {
    const src = lire('components/settings/PrivacyTab.tsx');
    expect(src).toMatch(/purgeIndisponible/);
    expect(src).toMatch(/valeurs par défaut/);
  });

  it("B-454 : une erreur sans action de reprise atteint quand même l'écran", () => {
    const src = lire('components/settings/SettingsModal.tsx');
    expect(src).not.toMatch(/\{error && retryOperation && \(/);
    expect(src).toMatch(/\{error && \(/);
  });

  it('B-459 : le magasin des factures est versionné et ne relit que ses filtres', () => {
    const src = lire('stores/invoiceStore.ts');
    expect(src).toMatch(/version: 1/);
    expect(src).not.toMatch(/\.\.\.courant, \.\.\.brut/);
  });

  it('B-463 : un lecteur audio ou vidéo avec commandes compte parmi les focusables', () => {
    expect(lire('hooks/useDialogFocusTrap.ts')).toMatch(/audio\[controls\], video\[controls\]/);
  });

  it("B-472 : le bouton d'action d'une notification navigue vers sa cible", () => {
    const src = lire('components/ui/NotificationCenter.tsx');
    expect(src).toMatch(/ouvrirLaCible\(actionUrl\)/);
    expect(src).not.toMatch(/Navigation via action_url possible ici/);
  });

  it('B-473 : le bouton Rafraîchir du panneau Email signale un échec', () => {
    const src = lire('components/email/EmailPanel.tsx');
    expect(src).toMatch(/async function loadLabels\(accountId: string\): Promise<boolean>/);
    expect(src).toMatch(/Impossible de rafraîchir les dossiers/);
  });

  it('B-474 : Réessayer relance la requête, pas la fenêtre', () => {
    const src = lire('components/prompts/PromptLibrary.tsx');
    expect(src).not.toMatch(/window\.location\.reload\(\)/);
    expect(src).toMatch(/onClick=\{\(\) => void chargerLaBibliotheque\(\)\}/);
  });

  it('B-483 : en démonstration, sources web et fichiers générés sont masqués', () => {
    const src = lire('components/chat/MessageList.tsx');
    expect(src).toMatch(/webSources: msg\.webSources\?\.map\(/);
    expect(src).toMatch(/file_name: maskText\(/);
  });

  it('B-485 : le centre de notifications ne triple pas ses annonces', () => {
    const src = lire('components/ui/NotificationCenter.tsx');
    expect(src).not.toMatch(/announceToScreenReader\(/);
    expect((src.match(/aria-live="polite"/g) ?? []).length).toBe(1);
  });

  it('B-490 : le sondage OAuth du CRM est annulé au démontage et parle quand il expire', () => {
    const src = lire('components/settings/CRMSyncPanel.tsx');
    expect(src).toMatch(/sondageOAuthRef/);
    expect(src).toMatch(/n’a pas été confirmée/);
  });

  it('B-491 : le sondage de réautorisation Google dit quand il abandonne', () => {
    const src = lire('components/calendar/CalendarPanel.tsx');
    expect(src).toMatch(/sondageReauthRef/);
    expect(src).toMatch(/n’a pas abouti/);
  });

  it("B-494 : un dossier connu mais non relu reste affiché, il n'est pas remplacé par « généraux »", () => {
    const src = lire('components/chat/ConversationProjectPicker.tsx');
    expect(src).toMatch(/dossierNonRelu/);
  });

  it('B-503 : le service email ne lève plus de chaînes techniques anglaises', () => {
    expect(lire('services/api/email.ts')).not.toMatch(/throw new Error\('Failed/);
  });

  it('B-506 : la tentative automatique de la liste des messages meurt avec la rubrique', () => {
    const src = lire('components/email/EmailList.tsx');
    expect(src).toMatch(/retryTimerRef/);
    expect(src).toMatch(/clearTimeout\(retryTimerRef\.current\)/);
  });
});
