/**
 * La carte de confirmation dit que l'agenda est COMMUN à tous les dossiers.
 *
 * Campagne cinq personas. Inès, psychologue, a validé la création de
 * « Séance Martin » en lisant la destination affichée : « Calendrier :
 * Mon calendrier ». Personne ne lui a dit que, depuis le dossier Ruiz, cette
 * ligne serait visible.
 *
 * Le leak est donc CONSENTI, pas subi — et c'est pire : elle a lu, elle a
 * compris ce qu'on lui montrait, et ce qu'on lui montrait était incomplet.
 *
 * Même geste que le lot A de la 0.54 : avouer avant de réparer. Le
 * cloisonnement de l'agenda arrive au lot suivant ; en attendant, la phrase
 * ne coûte rien et elle est vraie.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { ToolConfirmationCard } from './ToolConfirmationCard';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';

const confirmation = {
  confirmation_id: 'conf-1',
  conversation_id: 'conv-1',
  tool_name: 'create_calendar_event',
  arguments: {
    summary: 'Séance Martin',
    start: '2026-09-01T10:00:00',
    end: '2026-09-01T11:00:00',
    timezone: 'Europe/Paris',
    _confirmation_destination: { calendar_name: 'Mon calendrier', provider: 'local' },
  },
} as never;

describe('La destination annoncée dit ce qu’elle partage', () => {
  beforeEach(() => useToolConfirmationStore.setState({ pending: [] }));

  it('prévient que le calendrier est commun à tous les dossiers', () => {
    useToolConfirmationStore.setState({ pending: [confirmation] });
    render(<ToolConfirmationCard />);

    expect(screen.getByText(/Mon calendrier/)).toBeInTheDocument();
    expect(
      screen.getByText(/commun à tous (tes|vos) dossiers/i),
    ).toBeInTheDocument();
  });

  it('ne met pas cet avertissement sur un envoi d’e-mail', () => {
    useToolConfirmationStore.setState({
      pending: [
        {
          confirmation_id: 'conf-2', conversation_id: 'conv-1',
          tool_name: 'send_email',
          arguments: { to: 'a@b.c', subject: 'x', body: 'y' },
        } as never,
      ],
    });
    render(<ToolConfirmationCard />);

    expect(screen.queryByText(/commun à tous/i)).not.toBeInTheDocument();
  });
});
