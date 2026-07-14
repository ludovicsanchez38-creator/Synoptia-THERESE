import { describe, expect, it } from 'vitest';
import {
  buildClassicActionHref,
  buildClassicPanelHref,
  buildClassicPromptHref,
  buildClassicViewHref,
  consumeClassicPrompt,
  resolveClassicAction,
  resolveClassicPanel,
  resolveClassicPrompt,
  resolveClassicSettingsTab,
  resolveClassicView,
} from './classicNavigation';

describe('classicNavigation', () => {
  it('résout uniquement une vue classique connue', () => {
    expect(resolveClassicView('?view=crm')).toBe('crm');
    expect(resolveClassicView('?view=unknown')).toBeNull();
    expect(resolveClassicView('')).toBeNull();
  });

  it('construit un retour classique en retirant les paramètres du prototype', () => {
    const href = buildClassicViewHref(
      'http://127.0.0.1:1420/?prototype=conversation-canvas&scenario=today&debug=1',
      'calendar',
    );
    const url = new URL(href);

    expect(url.searchParams.get('interface')).toBe('classic');
    expect(url.searchParams.get('view')).toBe('calendar');
    expect(url.searchParams.get('prototype')).toBeNull();
    expect(url.searchParams.get('scenario')).toBeNull();
    expect(url.searchParams.get('debug')).toBe('1');
  });
});

describe('classic action and prompt navigation', () => {
  it('n’autorise que les actions classiques prévues', () => {
    expect(resolveClassicAction('?action=actions.open')).toBe('actions.open');
    expect(resolveClassicAction('?action=settings.open')).toBe('settings.open');
    expect(resolveClassicAction('?action=unknown')).toBeNull();
  });

  it('ouvre directement l’onglet de réglages demandé', () => {
    const href = buildClassicActionHref(
      'http://127.0.0.1:1420/?prototype=conversation-canvas&scenario=today',
      'settings.open',
      { settingsTab: 'privacy' },
    );
    const url = new URL(href);

    expect(url.searchParams.get('interface')).toBe('classic');
    expect(url.searchParams.get('view')).toBe('chat');
    expect(url.searchParams.get('action')).toBe('settings.open');
    expect(resolveClassicSettingsTab(url.search)).toBe('privacy');
    expect(url.searchParams.has('prototype')).toBe(false);
  });

  it('transporte un prompt édité vers le chat classique avec une limite sûre', () => {
    window.sessionStorage.setItem(
      'therese:classic-prompt-handoff',
      'Analyse mes fichiers et cite les sources.',
    );
    const href = buildClassicPromptHref(
      'http://127.0.0.1:1420/?prototype=conversation-canvas&scenario=today&action=settings.open',
      '  Analyse mes fichiers et cite les sources.  ',
    );
    const url = new URL(href);

    expect(url.searchParams.has('prompt')).toBe(false);
    expect(url.searchParams.get('handoff')).toBe('prompt');
    expect(consumeClassicPrompt(url.search)).toBe('Analyse mes fichiers et cite les sources.');
    expect(consumeClassicPrompt(url.search)).toBeNull();
    expect(url.searchParams.get('view')).toBe('chat');
    expect(url.searchParams.has('action')).toBe(false);
    expect(url.searchParams.has('scenario')).toBe(false);
  });

  it('lit encore un ancien lien prompt sans en générer de nouveau', () => {
    expect(resolveClassicPrompt('?prompt=Ancienne%20demande')).toBe('Ancienne demande');
  });

  it('ignore les onglets de réglages inconnus', () => {
    expect(resolveClassicSettingsTab('?settings_tab=ai')).toBe('ai');
    expect(resolveClassicSettingsTab('?settings_tab=secrets')).toBeNull();
  });

});

describe('classic panel navigation', () => {
  it('résout uniquement les panneaux classiques autorisés', () => {
    expect(resolveClassicPanel('?panel=board')).toBe('board');
    expect(resolveClassicPanel('?panel=atelier')).toBe('atelier');
    expect(resolveClassicPanel('?panel=unknown')).toBeNull();
  });

  it('construit le repli classique vers l’Atelier', () => {
    const href = buildClassicPanelHref(
      'http://127.0.0.1:1420/?prototype=conversation-canvas&scenario=atelier',
      'atelier',
    );
    const url = new URL(href);
    expect(url.searchParams.get('interface')).toBe('classic');
    expect(url.searchParams.get('panel')).toBe('atelier');
    expect(url.searchParams.has('prototype')).toBe(false);
    expect(url.searchParams.has('scenario')).toBe(false);
  });

  it('construit le repli classique vers le Board sans paramètres prototype', () => {
    const href = buildClassicPanelHref(
      'http://127.0.0.1:1420/?prototype=conversation-canvas&scenario=board',
      'board',
    );
    const url = new URL(href);
    expect(url.searchParams.get('interface')).toBe('classic');
    expect(url.searchParams.get('view')).toBe('chat');
    expect(url.searchParams.get('panel')).toBe('board');
    expect(url.searchParams.has('prototype')).toBe(false);
    expect(url.searchParams.has('scenario')).toBe(false);
  });
});
