/**
 * B2 — l'adresse et le téléphone doivent être saisissables là où l'artisan
 * passe réellement.
 *
 * Campagne dix personas, finding F2 : « Pas de champ Adresse à l'écran. J'ai
 * quand même envoyé l'adresse : elle est revenue vide. »
 *
 * La relecture de design a corrigé mon périmètre : le chemin de l'artisan n'est
 * pas la fiche contact du CRM, c'est le formulaire du PREMIER DEVIS, qui n'a
 * ni adresse ni téléphone (`InvoiceConversationCard.tsx`). Corriger le backend
 * sans ce formulaire aurait laissé la rupture intacte.
 *
 * Et le type `Contact` du frontend n'a pas `address` : un champ que le type
 * ignore ne remonte jamais jusqu'à l'API.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = join(__dirname, '..', '..');
const sansCommentaires = (chemin: string) =>
  readFileSync(join(RACINE, chemin), 'utf-8')
    .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/^\s*\/\/.*$/gm, '');

describe('B2 — l’adresse est saisissable là où le devis se crée', () => {
  it('le type Contact du frontend porte l’adresse', () => {
    const types = sansCommentaires('services/api/memory.ts');
    expect(types).toMatch(/address\??:\s*string/);
  });

  it('la fiche contact a un champ Adresse', () => {
    const modale = sansCommentaires('components/memory/ContactModal.tsx');
    expect(modale).toMatch(/address/i);
  });

  it('le formulaire du premier devis demande l’adresse ET le téléphone', () => {
    // Le chemin réel de l'artisan : « Crée le client de ce premier devis ».
    // Il n'avait que Prénom / Nom / Entreprise / Email.
    const canevas = sansCommentaires('components/prototype/InvoiceConversationCard.tsx');
    expect(canevas).toMatch(/address/i);
    expect(canevas).toMatch(/phone/i);
  });
});
