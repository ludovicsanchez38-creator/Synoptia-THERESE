/**
 * Lot 11 du cycle 3 (05/09/2026) : vingt défauts frontend confirmés par les
 * reproductions RP11 et RP12 (Sonnet). Gardes de source, une par bug, rouges
 * sur HEAD avant correctif.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const SRC = path.join(__dirname, '..');
const lire = (rel: string) => readFileSync(path.join(SRC, rel), 'utf-8');

describe('lot 11 - accessibilité, jetons et robustesse frontend', () => {
  it('B-402 : la confirmation de suppression de projet piège le focus', () => {
    const src = lire('components/memory/ProjectsPanel.tsx');
    expect(src).toMatch(/useDialogFocusTrap\(dialogRef, \{ active: Boolean\(deleteTarget\)/);
    expect(src).toMatch(/aria-labelledby="delete-project-title"[\s\S]*?ref=\{dialogRef\}|ref=\{dialogRef\}[\s\S]*?aria-labelledby="delete-project-title"/);
  });

  it('B-403 : le bouton de dépliage sécurité annonce son état et son contenu', () => {
    const src = lire('components/onboarding/SecurityStep.tsx');
    expect(src).toMatch(/aria-expanded=\{isExpanded\}/);
    expect(src).toMatch(/aria-controls=\{`security-detail-\$\{index\}`\}/);
    expect(src).toMatch(/id=\{`security-detail-\$\{index\}`\}/);
  });

  it('B-406 : le stepper de mission ne peint plus de RGBA littéral', () => {
    expect(lire('components/atelier/MissionStepper.tsx')).not.toMatch(/rgba\(/);
  });

  it('B-407 / B-437 : plus aucun alert() natif dans le formulaire de facture', () => {
    expect(lire('components/invoices/InvoiceForm.tsx')).not.toMatch(/\balert\(/);
  });

  it("B-408 : le voile de l'éditeur de signature ne ferme pas une saisie modifiée", () => {
    const src = lire('components/email/SignatureEditorModal.tsx');
    expect(src).not.toMatch(/backdrop-blur-sm \$\{Z_LAYER\.MODAL\}`\}\s*\n\s*onClick=\{onClose\}/);
    expect(src).toContain('fermerSiPropre');
  });

  it("B-410 : l'état vide distingue « rien » de « rien pour ce filtre »", () => {
    const src = lire('components/invoices/InvoicesPanel.tsx');
    expect(src).toMatch(/Aucun document ne correspond/);
    expect(src).toMatch(/Réinitialiser les filtres/);
  });

  it('B-414 : les jours hors mois gardent un texte lisible, sans opacity-50 sur la cellule', () => {
    const src = lire('components/calendar/CalendarView.tsx');
    expect(src).not.toMatch(/bg-background\/20 opacity-50/);
    expect(src).toMatch(/isCurrentMonth \? 'text-text' : 'text-text-muted'/);
  });

  it('B-415 : le sélecteur de modèle a une hauteur tactile', () => {
    const src = lire('components/chat/ChatInput.tsx');
    const bloc = src.slice(src.indexOf('aria-label="Modèle de conversation"'), src.indexOf('aria-label="Modèle de conversation"') + 600);
    expect(bloc).toMatch(/min-h-9/);
  });

  it('B-416 : le bouton de suppression de carte projet a un nom accessible et une cible', () => {
    const src = lire('components/memory/ProjectsKanban.tsx');
    expect(src).toMatch(/aria-label=\{`Supprimer \$\{project\.name\}`\}/);
    expect(src).not.toMatch(/className="p-1 rounded-md hover:bg-error\/20/);
  });

  it("B-417 : la racine du fil d'Ariane a un nom et une cible", () => {
    const src = lire('components/files/FileBrowser.tsx');
    expect(src).toMatch(/aria-label="Dossier racine"/);
  });

  it('B-418 : le bouton Contrôle des données ne se replie pas', () => {
    const src = lire('components/prototype/ConversationCanvasPrototype.tsx');
    expect(src).toMatch(/rounded-full border border-accent-cyan\/30 bg-accent-tint px-2\.5 py-1\.5 text-sm font-semibold text-accent hover:border-accent\/40 sm:flex whitespace-nowrap shrink-0/);
  });

  it('B-419 : le Centre de confiance dit « Paramètres »', () => {
    const src = lire('components/prototype/CapabilityCenter.tsx');
    expect(src).not.toContain('Réglages avancés');
    expect(src).toMatch(/onClick=\{onOpenAdvanced\}[^>]*>Paramètres</);
  });

  it('B-421 : le squelette de la modale Paramètres réserve la hauteur du contenu', () => {
    expect(lire('components/settings/SettingsModal.tsx')).not.toMatch(/justify-center h-32">\s*\n\s*<Spinner/);
  });

  it('B-424 : les segments de chemin du client agenda sont encodés', () => {
    const src = lire('services/api/calendar.ts');
    expect(src).not.toMatch(/\/calendars\/\$\{calendarId\}/);
    expect(src).not.toMatch(/\/events\/\$\{eventId\}/);
    expect(src).toMatch(/encodeURIComponent\(calendarId\)/);
    expect(src).toMatch(/encodeURIComponent\(eventId\)/);
  });

  it('B-426 : la revalidation du brief garde les données affichées', () => {
    const src = lire('components/prototype/usePrototypeReadData.ts');
    expect(src).not.toMatch(/setResource\(\{ status: 'loading', data: null, error: null \}\)/);
  });

  it("B-427 : l'exécution d'une commande est gardée par identifiant, jamais rejouée par un second rendu", () => {
    const src = lire('components/home/CommandExecutor.tsx');
    expect(src).not.toMatch(/\n {2}if \(command && !dynamicSkill[^\n]*\) \{\n {4}execute\(command\);/);
    expect(src).toMatch(/commandeExecuteeRef\.current !== command\.id/);
  });

  it("B-433 : réessayer une image relance la génération mémorisée", () => {
    const src = lire('components/home/CommandExecutor.tsx');
    expect(src).not.toMatch(/onRetry=\{\(\) => setImageState\(null\)\}/);
    expect(src).toContain('dernierPromptImageRef');
  });

  it('B-428 : un échec de mise à jour ou de suppression de projet est notifié', () => {
    const src = lire('components/memory/ProjectsPanel.tsx');
    expect((src.match(/addNotification\(/g) ?? []).length).toBeGreaterThanOrEqual(2);
  });

  it('B-435 : CompactMarkdown isole tout lien qui sort de la page', () => {
    const src = lire('components/ui/CompactMarkdown.tsx');
    expect(src).not.toMatch(/const external = \/\^https\?:\/i\.test\(href\);/);
  });
});
