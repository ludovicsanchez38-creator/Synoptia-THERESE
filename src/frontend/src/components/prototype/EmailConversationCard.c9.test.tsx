/**
 * B-810 (cycle 9) : sur une base sans aucun compte, le sous-titre de la carte
 * « Messages reçus » disait « Ta boîte connectée » pendant que son corps disait
 * « Aucun compte email connecté ».
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { EmailInboxCard } from './EmailConversationCard';

const props = { onRetry: vi.fn(), onOpenMessage: vi.fn(), onOpenClassic: vi.fn() };

describe('EmailInboxCard - B-810, le sous-titre dit l’état réel', () => {
  it('sans compte : « Aucune messagerie branchée », jamais « Ta boîte connectée »', () => {
    render(<EmailInboxCard {...props} resource={{ status: 'ready', error: null, data: { accounts: [], currentAccount: null, messages: [], failedMessages: 0 } } as never} />);
    expect(screen.queryByText('Ta boîte connectée')).toBeNull();
    expect(screen.getByText(/Aucune messagerie branchée/)).toBeInTheDocument();
  });

  it('pendant le chargement : « Chargement… », pas une promesse de connexion', () => {
    render(<EmailInboxCard {...props} resource={{ status: 'loading', error: null, data: null } as never} />);
    expect(screen.queryByText('Ta boîte connectée')).toBeNull();
  });
});
