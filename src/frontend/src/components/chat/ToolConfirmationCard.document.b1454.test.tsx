/**
 * B-1454 (recette P-146, lot 3) : la carte qui précède la création d'un
 * document s'intitulait « Confirmer l'action generate_document », le nom
 * technique de l'outil, et listait les clés brutes (format, content).
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { ToolConfirmationCard } from './ToolConfirmationCard';

vi.mock('../../services/api/chat', () => ({ confirmTool: vi.fn() }));

describe('B-1454 : la création d’un document se confirme en français', () => {
  beforeEach(() => useToolConfirmationStore.setState({ pending: [] }));

  it('titre et détails lisibles, sans nom d’outil', () => {
    useToolConfirmationStore.getState().add({
      confirmation_id: 'doc-1',
      tool_name: 'generate_document',
      arguments: { format: 'pptx', content: "## Offre d'accompagnement\n- Agenda partagé" },
    });
    render(<ToolConfirmationCard />);
    expect(screen.getByText('Confirmer la création du document')).toBeInTheDocument();
    expect(screen.getByText('Présentation PowerPoint (.pptx)')).toBeInTheDocument();
    expect(screen.queryByText(/generate_document/)).toBeNull();
    expect(screen.queryByText('content')).toBeNull();
  });
});
