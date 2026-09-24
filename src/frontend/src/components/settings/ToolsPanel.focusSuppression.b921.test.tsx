/**
 * B-921 : la question « Supprimer ce connecteur ? » se déclarait modale
 * (aria-modal) sans y mettre le focus ni le rendre au bouton d'origine : au
 * clavier, on restait derrière le voile.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const api = vi.hoisted(() => ({ deleteMCPServer: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listMCPServers: vi.fn().mockResolvedValue([
    { id: 's1', name: 'filesystem', command: 'npx', args: [], status: 'stopped', env: {}, created_at: '2026-09-01T10:00:00Z', tools: [] },
  ]),
  listMCPPresets: vi.fn().mockResolvedValue([]),
  getMCPStatus: vi.fn().mockResolvedValue({ total_servers: 1, running: 0, stopped: 1, error: 0 }),
  checkMCPPresetRequirements: vi.fn().mockResolvedValue({ all_satisfied: true, commands: {} }),
  deleteMCPServer: api.deleteMCPServer,
}));

import { ToolsPanel } from './ToolsPanel';

describe('ToolsPanel - B-921, focus de la question de suppression', () => {
  beforeEach(() => { vi.clearAllMocks(); _clearEscapeHandlers(); });

  it('le focus entre dans la question et revient à « Supprimer » après « Annuler »', async () => {
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByText('filesystem'));
    const supprimer = await screen.findByRole('button', { name: 'Supprimer' });
    supprimer.focus();
    fireEvent.click(supprimer);
    const question = await screen.findByRole('dialog', { name: 'Confirmer la suppression du connecteur' });

    await waitFor(() => expect(question.contains(document.activeElement)).toBe(true));

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Confirmer la suppression du connecteur' })).toBeNull());
    await waitFor(() => expect(document.activeElement).toBe(supprimer));
    expect(api.deleteMCPServer).not.toHaveBeenCalled();
  });
});
