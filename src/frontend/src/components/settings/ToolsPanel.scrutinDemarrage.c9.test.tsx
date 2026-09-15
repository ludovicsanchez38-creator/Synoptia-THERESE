/**
 * B-875 (cycle 9, relecteur U2) : quand un serveur MCP est « starting », un
 * scrutin toutes les 3 s appelle `refreshStatus`, qui ne relit que le statut
 * global, jamais la liste des serveurs : la condition d'arrêt ne pouvait pas
 * devenir fausse, et la carte du serveur restait « démarrage » à vie.
 */
import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listMCPServers: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listMCPServers: api.listMCPServers,
  listMCPPresets: vi.fn().mockResolvedValue([]),
  getMCPStatus: vi.fn().mockResolvedValue({ total_servers: 1, running: 0, stopped: 0, error: 0 }),
  checkMCPPresetRequirements: vi.fn().mockResolvedValue({ all_satisfied: true, commands: {} }),
}));

import { ToolsPanel } from './ToolsPanel';

const serveur = (status: string) => ({
  id: 's1', name: 'filesystem', command: 'npx', args: [], status, env: {}, created_at: '2026-09-01T10:00:00Z', tools: [],
});

describe('ToolsPanel - B-875, le scrutin d’un serveur en démarrage relit les serveurs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    api.listMCPServers.mockResolvedValueOnce([serveur('starting')]).mockResolvedValue([serveur('running')]);
  });
  afterEach(() => vi.useRealTimers());

  it('après un tour de scrutin, le serveur passe « running » et le scrutin s’arrête', async () => {
    render(<ToolsPanel onError={vi.fn()} />);
    await screen.findByText('filesystem');
    expect(api.listMCPServers).toHaveBeenCalledTimes(1);

    await act(async () => { vi.advanceTimersByTime(3100); await Promise.resolve(); });
    expect(api.listMCPServers).toHaveBeenCalledTimes(2);
    await act(async () => { await Promise.resolve(); });
    await act(async () => { vi.advanceTimersByTime(3100); await Promise.resolve(); });
    expect(api.listMCPServers).toHaveBeenCalledTimes(2);
  });
});
