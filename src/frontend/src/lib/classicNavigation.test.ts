import { describe, expect, it } from 'vitest';
import {
  buildClassicPanelHref,
  buildClassicViewHref,
  resolveClassicPanel,
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
