import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { CommonToolConfirmationLayer } from './CommonToolConfirmationLayer';

describe('CommonToolConfirmationLayer', () => {
  beforeEach(() => {
    useToolConfirmationStore.setState({ pending: [] });
  });

  it('ne montre aucune carte sans action sensible en attente', () => {
    render(<CommonToolConfirmationLayer />);
    expect(screen.queryByTestId('tool-confirmation')).toBeNull();
  });

  it('garde la confirmation visible indépendamment du contenu principal', () => {
    useToolConfirmationStore.setState({
      pending: [
        {
          confirmation_id: 'common-shell',
          tool_name: 'send_email',
          arguments: {
            to: 'merci@example.fr',
            subject: 'Merci',
            body: 'Merci pour votre retour.',
          },
        },
      ],
    });

    render(
      <>
        <div data-testid="interface-content">Canevas actif</div>
        <CommonToolConfirmationLayer />
      </>,
    );

    expect(screen.getByText(/Confirmer l[’']envoi de l[’']email/)).toBeInTheDocument();
    expect(screen.getByText('merci@example.fr')).toBeInTheDocument();
  });
});
