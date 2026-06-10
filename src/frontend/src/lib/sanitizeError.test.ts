import { describe, it, expect } from 'vitest';
import { sanitizeErrorMessage } from './sanitizeError';

describe('sanitizeErrorMessage (US-008 RES5-c)', () => {
  it('tronque les messages très longs', () => {
    const long = 'erreur '.repeat(200);
    expect(sanitizeErrorMessage(long).length).toBeLessThanOrEqual(201);
  });

  it('masque les chemins absolus (pas de fuite d’arborescence)', () => {
    const msg = 'ENOENT: /Users/synoptia/.therese/therese.db not found';
    const out = sanitizeErrorMessage(msg);
    expect(out).not.toContain('/Users/');
    expect(out).not.toContain('.therese');
    expect(out).toContain('[chemin]');
    expect(out).toContain('ENOENT');
  });

  it('masque aussi les chemins Windows', () => {
    const out = sanitizeErrorMessage('Erreur C:\\Users\\ludo\\therese.db verrouillé');
    expect(out).not.toContain('C:\\');
    expect(out).toContain('[chemin]');
  });

  it('laisse un message simple intact', () => {
    expect(sanitizeErrorMessage('Connexion impossible')).toBe('Connexion impossible');
  });
});
