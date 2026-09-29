/**
 * B-1738 : le tiroir reste large de 22 rem. Un titre long était coupé
 * (`truncate`) sans moyen de le lire. Le bouton qui l’ouvre porte le titre
 * complet (infobulle au survol et au focus) et son nom accessible aussi.
 */
import { render, screen } from '@testing-library/react';
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

describe('B-1738 : un titre long reste lisible dans le tiroir', () => {
  it('le bouton focalisable porte le titre complet, et le lecteur d’écran aussi', () => {
    poser(TITRE);
    const bouton = boutonDuTitre(TITRE);

    bouton.focus();
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

    bouton.focus();
    expect(bouton).toHaveAttribute('title', masque);
    expect(bouton).toHaveAccessibleName(expect.stringContaining(masque));
    expect(bouton.getAttribute('title')).not.toContain('Martin');
  });
});
