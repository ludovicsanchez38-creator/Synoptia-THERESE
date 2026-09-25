/**
 * P-117 (persona Claire, cycle 13), côté coque : « Compte rendu de la
 * séance » (Agenda) demande le parcours « Préparer un rendez-vous » sur
 * cette séance. La coque quitte la vue Agenda (pile alignée sur l'Accueil),
 * ouvre le parcours et lui passe l'événement.
 */
import { act, fireEvent, render, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const seances = vi.hoisted(() => ({ openEvent: vi.fn() }));
vi.mock('./usePrototypeMeetingData', async (importOriginal) => {
  const reel = await importOriginal<typeof import('./usePrototypeMeetingData')>();
  return {
    ...reel,
    usePrototypeMeetingData: () => ({
      resource: { status: 'loading', data: null, error: null },
      eventResource: null,
      refresh: vi.fn(),
      openEvent: seances.openEvent,
      retryEvent: vi.fn(),
      ensureDefaultCalendar: vi.fn(),
      createCalendarEvent: vi.fn(),
      createMeetingNote: vi.fn(),
    }),
  };
});
vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { meetingEventKey } from './usePrototypeMeetingData';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const seance = {
  id: 'e1', calendar_id: 'cal-1', summary: 'Séance Hélène', description: null, location: null,
  start_datetime: '2026-09-01T10:00:00', end_datetime: '2026-09-01T11:00:00', start_date: null, end_date: null,
  all_day: false, attendees: ['helene@example.com'], recurrence: null, status: 'confirmed', synced_at: null,
};

function ecranAffiche(): string | null {
  const vue = document.querySelector('[data-testid="conversation-canvas-prototype"]')?.getAttribute('data-embedded-view') ?? null;
  return vue === 'accueil' ? null : vue;
}

describe('P-117 : la coque ouvre la séance demandée depuis l’Agenda', () => {
  beforeEach(() => {
    seances.openEvent.mockClear();
    _clearEscapeHandlers();
    useNavigationStore.setState(useNavigationStore.getInitialState());
    useChatStore.setState({ isStreaming: false });
  });

  it('quitte l’Agenda, ouvre le parcours et lui passe la séance', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => {
      fireEvent.keyDown(window, { key: 'C', ctrlKey: true, metaKey: true, shiftKey: true });
    });
    await waitFor(() => expect(ecranAffiche()).toBe('calendar'));

    await act(async () => {
      window.dispatchEvent(new CustomEvent('therese:preparer-seance', { detail: { evenement: seance } }));
    });

    await waitFor(() => expect(ecranAffiche()).toBeNull());
    expect(useNavigationStore.getState().activeView).toBeNull();
    expect(seances.openEvent).toHaveBeenCalledWith(meetingEventKey(seance), seance);
    expect(document.querySelector('[data-testid="meeting-agenda-card"]')).not.toBeNull();
  });
});
