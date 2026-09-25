/**
 * BUG-042 / bug testeur « logo Mac (⌘) sous Windows » : la modale des raccourcis
 * doit afficher « Ctrl » sur Windows/Linux et le glyphe ⌘ seulement sur Mac.
 * Verrou anti-régression (le fix existe déjà, on le fige).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, afterEach } from 'vitest';
import { ShortcutsModal } from './ShortcutsModal';

const originalPlatform = Object.getOwnPropertyDescriptor(
  window.navigator,
  'platform'
);

function setPlatform(value: string) {
  Object.defineProperty(window.navigator, 'platform', {
    value,
    configurable: true,
  });
}

describe('ShortcutsModal - glyphe modificateur selon la plateforme', () => {
  afterEach(() => {
    if (originalPlatform) {
      Object.defineProperty(window.navigator, 'platform', originalPlatform);
    }
  });

  it('sur Windows : affiche « Ctrl », jamais le glyphe ⌘', () => {
    setPlatform('Win32');
    render(<ShortcutsModal isOpen={true} onClose={() => {}} />);

    // B-1375 : ⌘K porte le nom du dialogue qu'il ouvre.
    expect(screen.getByText('Rechercher une commande ou une capacité')).toBeTruthy();
    expect(document.body.textContent).not.toContain('⌘');
    expect(screen.getAllByText('Ctrl').length).toBeGreaterThan(0);
  });

  it('sur Mac : conserve le glyphe ⌘', () => {
    setPlatform('MacIntel');
    render(<ShortcutsModal isOpen={true} onClose={() => {}} />);

    expect(document.body.textContent).toContain('⌘');
  });
});

describe('P-095 : un raccourci se nomme par ce qu’il fait, pas par un prénom interne', () => {
  it('⌘⇧K ne dit plus « Katia » mais nomme l’action', () => {
    render(<ShortcutsModal isOpen onClose={() => {}} />);
    expect(screen.queryByText(/Katia/)).toBeNull();
    expect(screen.getByText(/Écrire à l’agent de l’Atelier/)).toBeInTheDocument();
  });
});
