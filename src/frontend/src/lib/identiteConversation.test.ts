/**
 * Dette relevée le 27/08 : rattacher un projet et envoyer un message dans la
 * même seconde.
 *
 * Rattacher un projet persiste la conversation : son identifiant devient celui
 * du serveur. Si un envoi était parti juste avant, il n'avait pas encore
 * d'identifiant à transmettre, le backend en crée donc une SECONDE, et le flux
 * la renvoie. Adopter cet identifiant-là écraserait la conversation qu'on
 * vient de rattacher : le projet posé côté serveur resterait sur une
 * conversation que plus personne n'affiche.
 *
 * Règle : on n'adopte une identité venue du flux que si la conversation n'en a
 * pas déjà une.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { doitAdopterIdentiteServeur } from './identiteConversation';

describe('Adopter l’identifiant renvoyé par le serveur', () => {
  it('l’adopte pour une conversation encore locale — le cas normal', () => {
    expect(doitAdopterIdentiteServeur('local-1', 'serveur-9', false)).toBe(true);
  });

  it('ne l’adopte pas si la conversation a déjà été enregistrée entre-temps', () => {
    expect(doitAdopterIdentiteServeur('serveur-1', 'serveur-9', true)).toBe(false);
  });

  it('n’adopte rien quand l’identifiant est le même', () => {
    expect(doitAdopterIdentiteServeur('serveur-1', 'serveur-1', false)).toBe(false);
  });

  it('n’adopte rien sans identifiant local ou serveur', () => {
    expect(doitAdopterIdentiteServeur(null, 'serveur-9', false)).toBe(false);
    expect(doitAdopterIdentiteServeur('local-1', '', false)).toBe(false);
  });

  it('est réellement branchée sur les deux chemins d’envoi', () => {
    // Ce chantier a déjà livré une autorité que personne n'appelait.
    const source = readFileSync(
      path.join(__dirname, '..', 'components', 'chat', 'ChatInput.tsx'),
      'utf8',
    );
    expect(source.split('doitAdopterIdentiteServeur(').length - 1).toBeGreaterThanOrEqual(2);
  });
});
