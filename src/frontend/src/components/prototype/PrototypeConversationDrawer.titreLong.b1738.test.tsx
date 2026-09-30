/**
 * B-1738 : le tiroir reste large de 22 rem. Un titre long était coupé
 * (`truncate`) sans moyen de le lire. Le bouton qui l’ouvre porte le titre
 * complet (infobulle au survol et au focus) et son nom accessible aussi.
 */
import { act, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useDemoStore } from '../../stores/demoStore';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';

const TITRE = 'Relance du devis de la boulangerie Martin, vitrine réfrigérée et planning de pose sur trois semaines';

function poser(titre: string) {
  useChatStore.setState({
    conversations: [{
      id: 'conversation-longue',
      title: titre,
      messages: [{ id: 'm1', role: 'user', content: 'Bonjour', timestamp: new Date() }],
      createdAt: new Date(),
      updatedAt: new Date(),
      synced: true,
    }],
    currentConversationId: null,
  });
  render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
}

function boutonDuTitre(titre: string): HTMLElement {
  const bouton = screen.getAllByRole('button').find((candidat) =>
    (candidat.textContent ?? '').includes(titre) && candidat.getAttribute('aria-haspopup') !== 'menu',
  );
  expect(bouton, 'le bouton de la conversation').toBeTruthy();
  return bouton as HTMLElement;
}

afterEach(() => {
  useChatStore.setState({ conversations: [], currentConversationId: null });
  useDemoStore.setState({ enabled: false, replacementMap: new Map() });
});

/** Même définition que la classe Tailwind `truncate` : jsdom n’a pas la feuille. */
function installerTruncate(): () => void {
  const style = document.createElement('style');
  style.textContent = '.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }';
  document.head.appendChild(style);
  return () => style.remove();
}

function titreEstCoupe(element: Element): boolean {
  const style = getComputedStyle(element);
  return style.whiteSpace === 'nowrap'
    || style.textOverflow === 'ellipsis'
    || style.overflow === 'hidden'
    || style.overflowX === 'hidden';
}

describe('B-1738 : un titre long reste lisible dans le tiroir', () => {
  it('au focus, le titre complet est visible, sans ellipse', () => {
    const retirer = installerTruncate();
    try {
      poser(TITRE);
      // L’entrée du tiroir laisse opacity à 0 dans jsdom : on la lève pour
      // juger le titre, pas l'animation.
      screen.getByTestId('prototype-conversation-drawer').style.opacity = '1';
      const bouton = boutonDuTitre(TITRE);
      const titre = bouton.querySelector('b');
      expect(titre).toBeTruthy();
      expect(titre).toBeVisible();
      expect(titre).toHaveTextContent(TITRE);
      expect(titreEstCoupe(titre as Element)).toBe(true);

      act(() => { bouton.focus(); });

      expect(bouton).toHaveFocus();
      expect(titre).toBeVisible();
      expect(titre).toHaveTextContent(TITRE);
      expect(titre?.getAttribute('aria-hidden')).not.toBe('true');
      expect(titreEstCoupe(titre as Element)).toBe(false);

      act(() => { bouton.blur(); });
      expect(titreEstCoupe(titre as Element)).toBe(true);
    } finally {
      retirer();
    }
  });

  it('le bouton focalisable porte le titre complet, et le lecteur d’écran aussi', () => {
    poser(TITRE);
    const bouton = boutonDuTitre(TITRE);

    act(() => { bouton.focus(); });
    expect(bouton).toHaveFocus();
    expect(bouton).toHaveAttribute('title', TITRE);
    expect(bouton.querySelector('b')).toHaveAttribute('title', TITRE);
    expect(bouton).toHaveAccessibleName(expect.stringContaining(TITRE));
    expect(bouton).toHaveAccessibleName(expect.stringContaining('1 message'));
    expect(screen.getByTestId('prototype-conversation-drawer').className).toMatch(/w-\[22rem\]/);
  });

  it('en démonstration, l’infobulle porte le pseudonyme, pas le vrai titre', () => {
    useDemoStore.setState({
      enabled: true,
      replacementMap: new Map([['Martin', 'Bernard']]),
    });
    const masque = TITRE.replace('Martin', 'Bernard');
    poser(TITRE);
    const bouton = boutonDuTitre(masque);

    act(() => { bouton.focus(); });
    expect(bouton).toHaveAttribute('title', masque);
    expect(bouton).toHaveAccessibleName(expect.stringContaining(masque));
    expect(bouton.getAttribute('title')).not.toContain('Martin');
  });

  it('au focus, en démonstration, le titre affiché est le pseudonyme', () => {
    const retirer = installerTruncate();
    try {
      useDemoStore.setState({
        enabled: true,
        replacementMap: new Map([['Martin', 'Bernard']]),
      });
      const masque = TITRE.replace('Martin', 'Bernard');
      poser(TITRE);
      screen.getByTestId('prototype-conversation-drawer').style.opacity = '1';
      const bouton = boutonDuTitre(masque);
      const titre = bouton.querySelector('b');

      act(() => { bouton.focus(); });

      expect(titre).toBeVisible();
      expect(titre).toHaveTextContent(masque);
      expect(titre?.textContent).not.toContain('Martin');
      expect(titreEstCoupe(titre as Element)).toBe(false);
    } finally {
      retirer();
    }
  });
});
