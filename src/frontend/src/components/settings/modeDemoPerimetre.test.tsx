/**
 * B-131 : le mode démo ne masque que ce qu'il connaît.
 *
 * Constaté dans l'application lancée le 01/09/2026 : sur six noms affichés
 * dans la même liste de tâches, cinq étaient remplacés par des personas
 * fictifs et « FORMACOM », tapé à la main dans un titre et absent du carnet
 * de contacts, restait en clair. Le masque est bâti depuis les contacts
 * chargés (demoStore.toggle -> buildReplacementMap) : il ne peut pas deviner
 * un nom propre qu'aucune fiche ne porte.
 *
 * Le défaut n'est donc pas le masque, c'est la promesse : le réglage
 * annonçait « Masque les noms et données clients par des personas fictifs »,
 * une garantie totale, et rien à l'écran ne disait où elle s'arrête. Celui
 * qui filme sa démonstration croit être couvert.
 *
 * Ce test verrouille la promesse honnête : dire d'où vient le masque, et
 * nommer ce qui reste en clair avec un exemple concret.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DemoModeSection } from './ProfileTab';

/** Le texte de la section, accents et espaces normalisés. */
function texteDeLaSection(): string {
  const section = screen.getByTestId('mode-demo-section');
  return (section.textContent ?? '').replace(/\s+/g, ' ');
}

describe('B-131 - le mode démo annonce son périmètre', () => {
  it("dit d'où vient le masque : les fiches contacts", () => {
    render(<DemoModeSection />);
    expect(texteDeLaSection()).toMatch(/contacts?/i);
  });

  it('nomme ce qui reste en clair', () => {
    render(<DemoModeSection />);
    const texte = texteDeLaSection();
    expect(
      /rest\w+ (visible|en clair|lisible)|en clair/i.test(texte),
      "la section ne dit nulle part qu'une partie de l'écran reste en clair : " +
        `texte affiché = « ${texte} »`,
    ).toBe(true);
  });

  it('donne un exemple concret du trou (un mot tapé à la main dans un titre)', () => {
    render(<DemoModeSection />);
    const texte = texteDeLaSection();
    expect(
      /titre|tapé|saisi|à la main/i.test(texte),
      "l'avertissement reste abstrait : sans exemple, l'utilisateur ne sait " +
        `pas quoi relire avant de filmer. Texte affiché = « ${texte} »`,
    ).toBe(true);
  });

  it('ne promet plus un masquage total des « données clients »', () => {
    render(<DemoModeSection />);
    expect(texteDeLaSection()).not.toMatch(
      /Masque les noms et données clients par des personas fictifs/i,
    );
  });
});
