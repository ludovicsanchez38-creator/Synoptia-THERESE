import { describe, it, expect } from 'vitest';
import { sanitizeEmailHtml } from './sanitizeEmailHtml';

describe('sanitizeEmailHtml - US-002 images distantes', () => {
  it('bloque par defaut les images distantes (http/https)', () => {
    const out = sanitizeEmailHtml('<p>Salut<img src="https://tracker.example.com/pixel.gif"></p>');
    // Plus de src LIVE (l'attribut src precede d'un espace) : seul data-blocked-src subsiste.
    expect(out).not.toMatch(/\ssrc="https:\/\//);
    expect(out).toContain('data-blocked-src="https://tracker.example.com/pixel.gif"');
    expect(out).toContain('data-remote-blocked="true"');
  });

  it('bloque aussi le http en clair', () => {
    const out = sanitizeEmailHtml('<img src="http://tracker.example.com/p.png">');
    expect(out).not.toMatch(/\ssrc="http:\/\//);
    expect(out).toContain('data-blocked-src="http://tracker.example.com/p.png"');
  });

  it('conserve les images inline data:', () => {
    const dataUri = 'data:image/png;base64,iVBORw0KGgo=';
    const out = sanitizeEmailHtml(`<img src="${dataUri}">`);
    expect(out).toContain(`src="${dataUri}"`);
    expect(out).not.toContain('data-remote-blocked');
  });

  it('opt-in explicite : allowRemoteImages garde la source distante', () => {
    const out = sanitizeEmailHtml('<img src="https://cdn.example.com/a.png">', {
      allowRemoteImages: true,
    });
    expect(out).toContain('src="https://cdn.example.com/a.png"');
    expect(out).not.toContain('data-blocked-src');
  });

  it('neutralise toujours les scripts et le style inline (regression)', () => {
    const out = sanitizeEmailHtml('<img src="https://x/y.png"><script>alert(1)</script><p style="position:fixed">x</p>');
    expect(out).not.toContain('<script');
    expect(out.toLowerCase()).not.toContain('style=');
  });
});
