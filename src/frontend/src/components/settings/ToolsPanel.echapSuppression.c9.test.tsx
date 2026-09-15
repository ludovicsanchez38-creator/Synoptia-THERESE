/**
 * B-896 (cycle 9, relecteur V3) : la modale « Supprimer ce connecteur ? »
 * (role dialog) n'avait aucune fermeture clavier : Échap ne faisait rien.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

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

describe('ToolsPanel - B-896, Échap referme la question de suppression', () => {
  beforeEach(() => { vi.clearAllMocks(); _clearEscapeHandlers(); });

  it('Échap équivaut à « Annuler »', async () => {
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByText('filesystem'));
    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer' }));
    await screen.findByRole('dialog', { name: 'Confirmer la suppression du connecteur' });

    let traite = false;
    act(() => { traite = runTopEscapeHandler(); });
    expect(traite).toBe(true);
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Confirmer la suppression du connecteur' })).toBeNull());
    expect(api.deleteMCPServer).not.toHaveBeenCalled();
  });
});
