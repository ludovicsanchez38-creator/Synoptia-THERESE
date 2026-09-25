/**
 * B-1473 : Fetch et Time se lancent par uvx. Sans uvx, l'installation
 * disait « Installe Node.js pour continuer » : le conseil de repli ne
 * connaissait que npx. Chaque commande manquante porte désormais son conseil.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const CONSEIL_UV = 'Installe uv depuis https://docs.astral.sh/uv/ (il fournit uvx), puis relance THÉRÈSE.';

const apiMocks = vi.hoisted(() => ({
  listMCPServers: vi.fn().mockResolvedValue([]),
  listMCPPresets: vi.fn(),
  getMCPStatus: vi.fn().mockResolvedValue({ total_servers: 0, running_servers: 0, total_tools: 0 }),
  checkMCPPresetRequirements: vi.fn(),
  installMCPPreset: vi.fn(),
  startMCPServer: vi.fn(),
}));

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...apiMocks,
}));

import { ToolsPanel } from './ToolsPanel';

describe('B-1473 : sans uvx, l’écran dit d’installer uv', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    apiMocks.listMCPPresets.mockResolvedValue([
      { id: 'time', name: 'Time', description: 'Conversions timezone', category: 'essentiels', command: 'uvx', args: ['mcp-server-time'] },
    ]);
    apiMocks.checkMCPPresetRequirements.mockResolvedValue({
      all_satisfied: false,
      commands: {
        npx: { available: true, path: '/usr/bin/npx', aide: 'Installe Node.js' },
        uvx: { available: false, path: null, aide: CONSEIL_UV },
      },
      help_message: null,
    });
  });

  it('le conseil de la commande manquante est affiché, pas celui de Node.js', async () => {
    const onError = vi.fn();
    render(<ToolsPanel onError={onError} />);
    fireEvent.click(await screen.findByRole('button', { name: /Presets/ }));
    expect(await screen.findByText(CONSEIL_UV)).toBeInTheDocument();

    fireEvent.click(await screen.findByRole('button', { name: 'Installer Time' }));
    expect(onError).toHaveBeenCalledWith(expect.stringContaining('https://docs.astral.sh/uv/'));
    expect(onError).not.toHaveBeenCalledWith(expect.stringContaining('Node.js'));
  });
});
