/**
 * B-282 - la cloche du centre de notifications tirait son nom du seul `title`.
 *
 * `title` n'est retenu qu'en dernier recours par le calcul de nom accessible,
 * et il ne s'affiche qu'au survol de la souris : au clavier, rien. RULES-DESIGN
 * §8 et §9.3 exigent un `aria-label` sur un bouton dont le seul enfant est une
 * icône. Deuxième effet mesuré ici : dès qu'un badge de non-lues apparaissait,
 * le nom du bouton devenait celui du badge (nom calculé depuis le contenu) et
 * le mot « Notifications » disparaissait. Le nom doit rester stable ET porter
 * le compte.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { NotificationCenter } from './NotificationCenter';
import { useNotificationStore } from '../../stores/notificationStore';

describe('B-282 - la cloche porte un nom accessible', () => {
  beforeEach(() => {
    useNotificationStore.setState({
      notifications: [],
      unreadCount: 0,
      isOpen: false,
      // Le sondage réseau n'a rien à faire ici : il n'est pas le sujet.
      startPolling: () => {},
      stopPolling: () => {},
    });
  });

  it('sans notification non lue, le bouton s’appelle « Notifications »', () => {
    render(<NotificationCenter />);

    const cloche = screen.getByRole('button', { name: 'Notifications' });
    expect(cloche.getAttribute('aria-label')).toBe('Notifications');
  });

  it('avec des non-lues, le nom garde « Notifications » et annonce le compte', () => {
    useNotificationStore.setState({ unreadCount: 3 });
    render(<NotificationCenter />);

    const cloche = screen.getByRole('button', { name: /^Notifications/ });
    expect(cloche).toHaveAccessibleName('Notifications, 3 non lues');
  });

  it('au-delà de 99, le badge reste compact mais le compte exact est annoncé', () => {
    useNotificationStore.setState({ unreadCount: 128 });
    render(<NotificationCenter />);

    expect(screen.getByText('99+')).toHaveAccessibleName('128 notifications non lues');
    expect(screen.getByRole('button', { name: 'Notifications, 128 non lues' })).toBeInTheDocument();
  });
});
