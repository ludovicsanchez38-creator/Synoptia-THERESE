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

describe('sanitizeEmailHtml - cycle 6 (D126) : pixel espion à protocole implicite', () => {
  it('bloque une image « //hôte/pixel.gif » (protocole hérité de la page, https dans l’application empaquetée)', () => {
    const html = sanitizeEmailHtml('<p>Bonjour</p><img src="//pisteur.example/pixel.gif" width="1" height="1">');
    expect(html).not.toMatch(/\ssrc="\/\/pisteur/);
    expect(html).toContain('data-blocked-src="//pisteur.example/pixel.gif"');
    expect(html).toMatch(/data-remote-blocked="true"/);
  });

  it('bloque aussi un srcset distant et une source sans schéma explicite', () => {
    const html = sanitizeEmailHtml('<img src="pixel.gif" srcset="https://pisteur.example/2x.gif 2x">');
    expect(html).not.toMatch(/srcset=/);
    expect(html).not.toMatch(/\ssrc="pixel\.gif"/);
  });

  it('garde les images data: inline', () => {
    const html = sanitizeEmailHtml('<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">');
    expect(html).toMatch(/src="data:image\/gif/);
  });
});
