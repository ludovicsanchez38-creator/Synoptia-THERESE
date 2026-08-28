/**
 * Chantier A-texte : la pastille « local » du chat ne doit pas promettre plus
 * que le reste de l'application.
 *
 * Son infobulle disait « le traitement est resté sur ta machine, rien ne
 * sort » — exactement la phrase bannie du prompt système par ce même lot. Sans
 * ce test, un revert de l'infobulle serait invisible (relevé par la
 * revalidation Grok : « zéro test de rendu, un revert y est invisible »).
 *
 * On lit le source ici, faute de pouvoir monter MessageBubble sans un message
 * complet et ses stores : c'est un filet, pas une preuve d'affichage. Le
 * commentaire de ce fichier vaut avertissement pour qui voudra le durcir.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  join(__dirname, 'MessageBubble.tsx'),
  'utf-8',
).replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

describe('La pastille « réponse locale » ne promet pas que rien ne sort', () => {
  it('n’affirme plus « rien ne sort »', () => {
    expect(source).not.toMatch(/rien ne sort/i);
  });

  it('dit ce qui reste local, sans généraliser', () => {
    expect(source).toMatch(/le traitement est resté sur ta machine/i);
  });
});
