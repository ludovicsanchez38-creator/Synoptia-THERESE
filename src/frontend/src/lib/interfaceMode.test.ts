import { describe, expect, it } from 'vitest';
import { resolveInterfaceMode, resolveRuntimeInterfaceMode } from './interfaceMode';

describe('resolveInterfaceMode', () => {
  it("conserve l'interface classique par défaut", () => {
    expect(resolveInterfaceMode()).toBe('classic');
  });

  it("active l'interface 0.40 avec le nouveau paramètre d'URL", () => {
    expect(resolveInterfaceMode({ search: '?interface=conversation-canvas' })).toBe('conversation-canvas');
  });

  it("conserve la compatibilité avec l'URL du prototype", () => {
    expect(resolveInterfaceMode({ search: '?prototype=conversation-canvas&scenario=today' })).toBe('conversation-canvas');
  });

  it('permet un build bêta activé explicitement', () => {
    expect(resolveInterfaceMode({ buildMode: 'conversation-canvas' })).toBe('conversation-canvas');
  });

  it('permet une activation locale persistante pour un bêta-testeur', () => {
    expect(resolveInterfaceMode({ storedMode: 'conversation-canvas' })).toBe('conversation-canvas');
  });

  it("permet de forcer l'interface classique pour revenir en arrière", () => {
    expect(resolveInterfaceMode({
      search: '?interface=classic',
      buildMode: 'conversation-canvas',
      storedMode: 'conversation-canvas',
    })).toBe('classic');
  });

  it('ignore les valeurs inconnues et revient au mode sûr', () => {
    expect(resolveInterfaceMode({
      search: '?interface=experimental',
      buildMode: 'enabled',
      storedMode: 'new',
    })).toBe('classic');
  });
});

describe('resolveRuntimeInterfaceMode', () => {
  it('autorise le prototype pendant le développement local', () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: true,
      search: '?interface=conversation-canvas',
    })).toBe('conversation-canvas');
  });

  it('force toujours l’interface classique dans un build distribuable', () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: false,
      search: '?interface=conversation-canvas',
      buildMode: 'conversation-canvas',
      storedMode: 'conversation-canvas',
    })).toBe('classic');
  });
});
