/**
 * C1 — le sélecteur de périmètre doit dire ce qu'il cloisonne.
 *
 * Campagne dix personas, finding F5 de l'avocat. Le seul libellé qui parle de
 * cloisonnement dit « Documents consultés par cette conversation ». Les
 * fichiers étaient bien cloisonnés ; les fiches contacts, non — et c'est dans
 * une fiche qu'il avait écrit le secret médical de sa cliente.
 *
 * La relecture de design a imposé l'ordre : C1 vient APRÈS le mode cabinet.
 * « Renommer en "Dossier de cette conversation" pendant que les fiches fuient
 * remplace un mensonge étroit par un mensonge large. »
 *
 * Le mode existe désormais (C3), et le périmètre d'une fiche est un choix
 * (C2). Le libellé peut donc nommer le dossier — sans promettre une étanchéité
 * qui dépend d'un réglage.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(join(__dirname, 'ConversationProjectPicker.tsx'), 'utf-8')
  .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/^\s*\/\/.*$/gm, '');

describe('Le sélecteur de périmètre nomme ce qu’il cloisonne', () => {
  it('ne parle plus seulement de « documents »', () => {
    // Les fichiers ne sont pas la seule chose rattachée à un dossier : les
    // fiches contacts et les projets le sont aussi depuis C2.
    expect(source).not.toContain('Documents consultés par cette conversation');
  });

  it('nomme le dossier SANS promettre une étanchéité qui dépend d’un réglage', () => {
    // Relecture : « Dossier de cette conversation » tout court remplaçait un
    // mensonge étroit (« documents ») par un mensonge large — le carnet reste
    // partagé tant que le mode cabinet est éteint, ce qui est le défaut.
    expect(source).toMatch(/Dossier de cette conversation/);
    expect(source).toMatch(/carnet partagé/);
  });

  it('garde une étiquette accessible cohérente avec le texte visible', () => {
    // L'aria-label et le sr-only doivent dire la même chose : c'est ce libellé
    // qu'entend un utilisateur au lecteur d'écran.
    const etiquettes = source.match(/Dossier de cette conversation/g) ?? [];
    expect(etiquettes.length).toBeGreaterThanOrEqual(2);
  });
});
