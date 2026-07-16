import { describe, expect, it } from 'vitest';
import { resolveInterfaceMode, resolveRuntimeInterfaceMode } from './interfaceMode';

describe('resolveInterfaceMode', () => {
  it("active l'interface 0.40 par défaut", () => {
    expect(resolveInterfaceMode()).toBe('conversation-canvas');
  });

  it("active l'interface 0.40 avec le nouveau paramètre d'URL", () => {
    expect(resolveInterfaceMode({ search: '?interface=conversation-canvas' })).toBe('conversation-canvas');
  });

  it("conserve la compatibilité avec l'URL du prototype", () => {
    expect(resolveInterfaceMode({ search: '?prototype=conversation-canvas&scenario=today' })).toBe('conversation-canvas');
  });

  it('respecte la variable de mode en développement', () => {
    expect(resolveInterfaceMode({ buildMode: 'conversation-canvas' })).toBe('conversation-canvas');
  });

  it('respecte un choix conversationnel explicite et persistant', () => {
    expect(resolveInterfaceMode({ storedMode: 'conversation-canvas' })).toBe('conversation-canvas');
  });

  it('respecte un choix classique explicite sans forçage de développement', () => {
    expect(resolveInterfaceMode({ storedMode: 'classic' })).toBe('classic');
  });

  it("permet de forcer l'interface classique pour revenir en arrière", () => {
    expect(resolveInterfaceMode({
      search: '?interface=classic',
      buildMode: 'conversation-canvas',
      storedMode: 'conversation-canvas',
    })).toBe('classic');
  });

  it('ignore les valeurs inconnues et revient au nouveau mode par défaut', () => {
    expect(resolveInterfaceMode({
      search: '?interface=experimental',
      buildMode: 'enabled',
      storedMode: 'new',
    })).toBe('conversation-canvas');
  });
});

describe('resolveRuntimeInterfaceMode', () => {
  it("autorise les forçages par URL et variable de build pendant le développement local", () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: true,
      isExplicitDevelopmentBuild: true,
      search: '?interface=conversation-canvas',
      buildMode: 'classic',
      storedMode: 'classic',
    })).toBe('conversation-canvas');

    expect(resolveRuntimeInterfaceMode({
      isDevelopment: true,
      isExplicitDevelopmentBuild: true,
      buildMode: 'classic',
      storedMode: 'conversation-canvas',
    })).toBe('classic');
  });

  it('respecte le choix mémorisé dans un build de production', () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: false,
      isExplicitDevelopmentBuild: false,
      storedMode: 'conversation-canvas',
    })).toBe('conversation-canvas');
  });

  it("ignore l'URL et la variable de build en production", () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: false,
      isExplicitDevelopmentBuild: false,
      search: '?interface=conversation-canvas',
      buildMode: 'conversation-canvas',
      storedMode: 'classic',
    })).toBe('classic');
  });

  it("utilise l'interface 0.40 par défaut si le choix de production est absent ou invalide", () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: false,
      isExplicitDevelopmentBuild: false,
    })).toBe('conversation-canvas');
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: false,
      isExplicitDevelopmentBuild: false,
      storedMode: 'experimental',
    })).toBe('conversation-canvas');
  });

  it('réserve aussi les forçages dev au serveur Vite identifié par le flag explicite', () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: true,
      isExplicitDevelopmentBuild: false,
      search: '?interface=conversation-canvas',
      buildMode: 'conversation-canvas',
      storedMode: 'classic',
    })).toBe('classic');

    expect(resolveRuntimeInterfaceMode({
      isDevelopment: true,
      isExplicitDevelopmentBuild: false,
      search: '?interface=classic',
      buildMode: 'classic',
      storedMode: 'conversation-canvas',
    })).toBe('conversation-canvas');
  });

  it('respecte un choix classique explicite dans un build de production', () => {
    expect(resolveRuntimeInterfaceMode({
      isDevelopment: false,
      isExplicitDevelopmentBuild: false,
      storedMode: 'classic',
    })).toBe('classic');
  });
});
