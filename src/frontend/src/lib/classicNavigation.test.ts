import { describe, expect, it } from 'vitest';
import { buildClassicViewHref, resolveClassicView } from './classicNavigation';

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
