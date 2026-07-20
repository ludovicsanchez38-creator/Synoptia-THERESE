/**
 * BUG-139 (suite, 20/07/2026) : les commandes / de navigation portent un
 * actionId et s'exécutent directement à la sélection (dictée, zéro
 * aller-retour), au lieu d'insérer un message-action à envoyer.
 */
import { describe, expect, it } from 'vitest';
import { SLASH_COMMANDS } from './SlashCommandsMenu';
import { getActions } from '../../lib/actionRegistry';

const NAVIGATION_IDS: Record<string, string> = {
  'ouvrir-email': 'email.open',
  'ouvrir-crm': 'crm.open',
  'ouvrir-memoire': 'memory.open',
  'ouvrir-calendrier': 'calendar.open',
  'ouvrir-taches': 'tasks.open',
  'ouvrir-documents': 'documents.open',
  'ouvrir-facturation': 'invoices.open',
};

describe('SLASH_COMMANDS - navigation directe (BUG-139 suite)', () => {
  it('chaque commande de navigation porte un actionId connu du registre', () => {
    const registryIds = new Set(getActions().map((a) => a.id));
    for (const [slashId, actionId] of Object.entries(NAVIGATION_IDS)) {
      const command = SLASH_COMMANDS.find((c) => c.id === slashId);
      expect(command, `commande ${slashId} absente`).toBeDefined();
      expect(command?.actionId, `actionId manquant sur ${slashId}`).toBe(actionId);
      expect(registryIds.has(actionId), `${actionId} inconnu du registre`).toBe(true);
    }
  });

  it('les commandes de production et de variables restent des insertions', () => {
    for (const id of ['produire-docx', 'produire-xlsx', 'produire-pptx', 'variable-creer', 'variables']) {
      const command = SLASH_COMMANDS.find((c) => c.id === id);
      expect(command, `commande ${id} absente`).toBeDefined();
      expect(command?.actionId).toBeUndefined();
    }
  });
});
