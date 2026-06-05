import { describe, it, expect, beforeEach, vi } from 'vitest';
import { pushEscapeHandler, runTopEscapeHandler, _clearEscapeHandlers } from './escapeStack';

describe('escapeStack (overlays internes aux vues — KO Syn 1.1/1.2/1.3)', () => {
  beforeEach(() => _clearEscapeHandlers());

  it('sans handler, runTop retourne false (Échap continue vers la pile globale)', () => {
    expect(runTopEscapeHandler()).toBe(false);
  });

  it('déclenche le handler le plus récent et retourne true', () => {
    const a = vi.fn();
    const b = vi.fn();
    pushEscapeHandler(a);
    pushEscapeHandler(b);
    expect(runTopEscapeHandler()).toBe(true);
    expect(b).toHaveBeenCalledTimes(1);
    expect(a).not.toHaveBeenCalled(); // seul le plus en avant
  });

  it('la fonction de désinscription retire le handler', () => {
    const a = vi.fn();
    const off = pushEscapeHandler(a);
    off();
    expect(runTopEscapeHandler()).toBe(false);
    expect(a).not.toHaveBeenCalled();
  });

  it('désinscription au milieu de la pile ne touche pas les autres', () => {
    const a = vi.fn();
    const b = vi.fn();
    const offA = pushEscapeHandler(a);
    pushEscapeHandler(b);
    offA();
    expect(runTopEscapeHandler()).toBe(true);
    expect(b).toHaveBeenCalledTimes(1);
  });
});
