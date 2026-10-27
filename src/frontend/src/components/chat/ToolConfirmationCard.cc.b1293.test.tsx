/**
 * B-1293 : la carte « Confirmer l'envoi de l'email » cachait la copie (Cc)
 * que l'outil send_email transmet au fournisseur. Un mail lu dans le fil
 * (« mets compta@… en copie ») suffisait à faire partir le message chez une
 * adresse que l'utilisateur n'avait jamais vue avant de cliquer « Envoyer ».
 * La carte montre désormais tout ce qui part : Cc, et tout autre argument
 * public qu'elle ne sait pas nommer.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToolConfirmationCard } from './ToolConfirmationCard';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';

vi.mock('../../services/api/chat', () => ({
  confirmTool: vi.fn().mockResolvedValue({ status: 'executed', tool_name: 'send_email', result: 'ok' }),
}));

function poser(args: Record<string, unknown>) {
  useToolConfirmationStore.getState().add({
    confirmation_id: 'cc-1',
    tool_name: 'send_email',
    arguments: args,
  });
}

describe('ToolConfirmationCard, copie visible (B-1293)', () => {
  beforeEach(() => {
    useToolConfirmationStore.setState({ pending: [] });
  });

  it('affiche la copie (Cc) qui partira avec le message', () => {
    poser({ to: 'client@exemple.fr', subject: 'Devis', body: 'Bonjour', cc: 'compta@pirate.example' });
    render(<ToolConfirmationCard />);

    expect(screen.queryByText('compta@pirate.example')).toBeTruthy();
    expect(screen.queryByText(/Copie/)).toBeTruthy();
  });

  it('affiche plusieurs adresses en copie', () => {
    poser({ to: 'a@x.fr', subject: 'S', body: 'B', cc: 'un@x.fr, deux@y.fr' });
    render(<ToolConfirmationCard />);

    expect(screen.queryByText('un@x.fr, deux@y.fr')).toBeTruthy();
  });

  it("n'affiche pas de ligne de copie quand il n'y en a pas", () => {
    poser({ to: 'a@x.fr', subject: 'S', body: 'B' });
    render(<ToolConfirmationCard />);

    expect(screen.queryByText(/Copie/)).toBeNull();
  });

  it('montre tout argument public inconnu au lieu de le taire', () => {
    poser({ to: 'a@x.fr', subject: 'S', body: 'B', bcc: 'cache@pirate.example', reply_to: 'retour@pirate.example' });
    render(<ToolConfirmationCard />);

    expect(screen.queryByText('cache@pirate.example')).toBeTruthy();
    expect(screen.queryByText('retour@pirate.example')).toBeTruthy();
  });

  it('ne répète pas les champs déjà affichés ni les clés internes', () => {
    poser({
      to: 'a@x.fr', subject: 'Sujet unique', body: 'B', is_html: false,
      _confirmation_destination: { account: 'moi@x.fr' },
    });
    render(<ToolConfirmationCard />);

    expect(screen.getAllByText('Sujet unique')).toHaveLength(1);
    expect(screen.queryByText(/_confirmation_destination/)).toBeNull();
  });
});
