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
    // B-1196 : le nom s'affiche parfois avant que l'effet ne pose le scrutin ;
    // avancer le temps à ce moment ne déclenchait rien (1 échec sur 60).
    for (let i = 0; i < 20 && vi.getTimerCount() === 0; i++) {
      await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
    }
    expect(vi.getTimerCount()).toBeGreaterThan(0);

    await act(async () => { vi.advanceTimersByTime(3100); await Promise.resolve(); });
    expect(api.listMCPServers).toHaveBeenCalledTimes(2);
    // B-1196 : une seule microtâche ne suffisait pas toujours à propager le
    // « running » (1 échec sur 6 à 10) ; une vraie tâche (setTimeout n'est pas
    // simulé ici) vide toute la chaîne de promesses du rafraîchissement.
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
    await act(async () => { vi.advanceTimersByTime(3100); await Promise.resolve(); });
    expect(api.listMCPServers).toHaveBeenCalledTimes(2);
  });
});
