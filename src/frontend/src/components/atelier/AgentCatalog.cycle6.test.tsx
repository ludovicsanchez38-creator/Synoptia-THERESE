/**
 * Cycle 6, lecteur #112 (AgentCatalog.tsx) : quand la lecture des profils
 * échouait, le catch posait les profils de repli ET effaçait l'erreur ; l'écran
 * d'erreur ne pouvait jamais apparaître et le repli passait pour le catalogue.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  getAgentProfiles: vi.fn().mockRejectedValue(new Error('boom')),
  getAgentConfig: vi.fn().mockResolvedValue(null),
}));

import { AgentCatalog } from './AgentCatalog';

describe('#112 : un catalogue de repli est annoncé comme tel', () => {
  it('affiche les profils de repli et une alerte qui dit que le catalogue n’a pas été lu', async () => {
    render(<AgentCatalog onSelectAgent={vi.fn()} />);
    expect(await screen.findByText('Chercheur Web')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/Catalogue des agents non lu/);
  });
});
