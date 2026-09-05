/**
 * Lot 15 (05/09/2026) : gardes de source des correctifs statiques du lot,
 * reproduits par RP18. Chaque garde nomme son bug ; les comportements ont
 * leurs propres tests à côté des composants.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const racine = resolve(__dirname, '..');
const lire = (chemin: string) => readFileSync(resolve(racine, chemin), 'utf8');

describe('lot 15 : gardes de source', () => {
  it('B-563 : la coque câble onOpenItem et résout la cible d’un point d’attention', () => {
    const coque = lire('components/prototype/ConversationCanvasPrototype.tsx');
    expect(coque).toContain('onOpenItem={');
    expect(coque).toContain('destinationDuPoint(');
  });

  it('B-562 : la coque affiche un indice de défilement au-dessus du composeur', () => {
    const coque = lire('components/prototype/ConversationCanvasPrototype.tsx');
    expect(coque).toContain('<IndiceDeDefilement');
  });

  it('B-564 : les espaces réservés de la fiche contact ne ressemblent pas à des données', () => {
    const modale = lire('components/memory/ContactModal.tsx');
    expect(modale).not.toContain('14 chemin des Oliviers');
    expect(modale).not.toContain('+33 6 12 34 56 78');
  });

  it('B-567 : la palette ne propose plus deux entrées quasi identiques pour la facturation', () => {
    const centre = lire('components/prototype/CapabilityCenter.tsx');
    expect(centre).toContain("title: 'Facturer un client'");
    expect(centre).not.toContain("title: 'Devis et factures', icon: Receipt, scenario: 'invoice'");
  });

  it('B-571 : une conversation créée implicitement par addMessage n’est pas réputée synchronisée', () => {
    const store = lire('stores/chatStore.ts');
    const implicite = store.slice(store.indexOf('// Create conversation if none exists'));
    expect(implicite.slice(0, 900)).toContain('synced: false');
  });

  it('B-573 : le message d’aperçu distingue un agenda local d’un fournisseur qui invite', () => {
    const formulaire = lire('components/calendar/EventForm.tsx');
    expect(formulaire).toContain('ne peut pas leur envoyer d’invitation');
  });

  it('B-574 : le canevas Facturer charge le même plafond de contacts que le formulaire et sait qu’il est tronqué', () => {
    const donnees = lire('components/prototype/usePrototypeInvoiceData.ts');
    expect(donnees).toContain('PLAFOND_CONTACTS');
    expect(donnees).toContain('contactsTronques');
    expect(donnees).not.toContain('listContacts(0, 100)');
  });

  it('B-577 : la vue Mois trie les événements d’un jour par heure', () => {
    const vue = lire('components/calendar/CalendarView.tsx');
    expect(vue).toContain('trierLesEvenementsDuJour(');
  });

  it('B-578 : les boutons icône seule de l’agenda et des factures portent un nom', () => {
    expect(lire('components/calendar/EventForm.tsx')).toContain('aria-label="Retour"');
    const detail = lire('components/calendar/EventDetail.tsx');
    expect(detail).toContain('aria-label="Retour"');
    expect(detail).toContain('aria-label="Modifier l’événement"');
    expect(detail).toContain('aria-label="Supprimer l’événement"');
    const facture = lire('components/invoices/InvoiceForm.tsx');
    expect(facture).toContain('aria-label="Fermer"');
    expect(facture).toContain('aria-label={`Supprimer la ligne ${index + 1}`}');
  });
});
