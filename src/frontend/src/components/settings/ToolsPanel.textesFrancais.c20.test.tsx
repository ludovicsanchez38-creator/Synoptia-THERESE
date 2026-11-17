import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToolsPanel } from './ToolsPanel';
import * as api from '../../services/api';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

vi.mock('../../services/api', async (original) => ({
  ...(await original<typeof import('../../services/api')>()),
  listMCPServers: vi.fn(), listMCPPresets: vi.fn(), getMCPStatus: vi.fn(),
  checkMCPPresetRequirements: vi.fn(), installMCPPreset: vi.fn(), deleteMCPServer: vi.fn(),
}));

const serveur: api.MCPServer = {
  id: 'horloge-test', name: 'Horloge', command: 'uvx', args: ['mcp-server-time'],
  env: {}, enabled: true, status: 'stopped', tools: [], error: null, created_at: '',
};
const preset: api.MCPPreset = {
  id: 'time', name: 'Horloge', command: 'uvx', args: ['mcp-server-time'],
  description: 'Heure locale', category: 'essentiels', installed: false,
};

beforeEach(() => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  vi.mocked(api.listMCPServers).mockResolvedValue([serveur]);
  vi.mocked(api.listMCPPresets).mockResolvedValue([preset]);
  vi.mocked(api.getMCPStatus).mockResolvedValue({ total_servers: 1, running_servers: 0, total_tools: 0, servers: {} });
  vi.mocked(api.checkMCPPresetRequirements).mockResolvedValue({ all_satisfied: true, commands: {}, help_message: null });
  vi.mocked(api.deleteMCPServer).mockResolvedValue(undefined);
});

describe('Textes des connecteurs, cycle 20', () => {
  it('R2-10 : un connecteur starting annonce son démarrage en cours', async () => {
    vi.mocked(api.listMCPServers).mockResolvedValue([{ ...serveur, status: 'starting' }]);
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Presets' }));
    expect(screen.getByRole('img', { name: 'Installé : démarrage en cours' })).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /Installé mais inactif/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Horloge est installé' })).toBeDisabled();
  });

  it.each(['stopped', 'error'] as const)('B-1965 : le connecteur %s porte un état inactif accessible', async (status) => {
    vi.mocked(api.listMCPServers).mockResolvedValue([{ ...serveur, status }]);
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Presets' }));
    expect(screen.getByRole('img', { name: 'Installé mais inactif : à démarrer depuis les connecteurs' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Horloge est installé' })).toBeDisabled();
  });

  it('B-1965 : un connecteur actif ne porte pas l’annonce inactif', async () => {
    vi.mocked(api.listMCPServers).mockResolvedValue([{ ...serveur, status: 'running' }]);
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Presets' }));
    expect(screen.queryByRole('img', { name: /Installé mais inactif/ })).not.toBeInTheDocument();
  });
  it('B-1964 : la confirmation nomme le connecteur choisi parmi plusieurs', async () => {
    vi.mocked(api.listMCPServers).mockResolvedValue([serveur, { ...serveur, id: 'agenda-test', name: 'Agenda', status: 'error' }]);
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer Agenda' }));
    const dialogue = screen.getByRole('dialog', { name: 'Confirmer la suppression du connecteur' });
    expect(within(dialogue).getByRole('heading')).toHaveTextContent('Supprimer Agenda ?');
    expect(dialogue).toHaveAccessibleDescription('Supprimer Agenda ? Cette action est irréversible.');
    expect(api.deleteMCPServer).not.toHaveBeenCalled();
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Supprimer' }));
    await waitFor(() => expect(api.deleteMCPServer).toHaveBeenCalledWith('agenda-test'));
  });
  it.each(['uvx', 'npx', 'python'])('B-1963 : un échec de %s sans motif ne suppose pas Node.js absent', async (command) => {
    vi.mocked(api.listMCPServers).mockResolvedValue([]);
    vi.mocked(api.listMCPPresets).mockResolvedValue([{ ...preset, command }]);
    vi.mocked(api.installMCPPreset).mockResolvedValue({ ...serveur, command, status: 'error' });
    const onError = vi.fn();
    render(<ToolsPanel onError={onError} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Presets' }));
    fireEvent.click(screen.getByRole('button', { name: 'Installer Horloge' }));
    await waitFor(() => expect(onError).toHaveBeenCalled());
    expect(onError).toHaveBeenCalledWith('Horloge installé mais erreur au démarrage : Consulte les détails du connecteur, puis réessaie de le démarrer.');
  });

  it('B-1963 : conserve le motif de démarrage communiqué par le moteur', async () => {
    vi.mocked(api.listMCPServers).mockResolvedValue([]);
    vi.mocked(api.installMCPPreset).mockResolvedValue({ ...serveur, status: 'error', error: 'Délai de démarrage dépassé' });
    const onError = vi.fn();
    render(<ToolsPanel onError={onError} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Presets' }));
    fireEvent.click(screen.getByRole('button', { name: 'Installer Horloge' }));
    await waitFor(() => expect(onError).toHaveBeenCalledWith('Horloge installé mais erreur au démarrage : Délai de démarrage dépassé'));
  });
  it.each([0, 1, 2])('B-1962 : les décomptes de %i outils sont en français', async (nombre) => {
    const tools = Array.from({ length: nombre }, (_, i) => ({
      name: `outil-${i}`, description: 'Outil de test', input_schema: {}, server_id: serveur.id,
    }));
    vi.mocked(api.listMCPServers).mockResolvedValue([{ ...serveur, tools }]);
    vi.mocked(api.getMCPStatus).mockResolvedValue({ total_servers: 1, running_servers: 1, total_tools: nombre, servers: {} });
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByText('Horloge'));
    const compte = `${nombre} outil${nombre === 1 ? '' : 's'}`;
    expect(screen.getByText(new RegExp(`${compte} disponible`))).toBeInTheDocument();
    expect(screen.getByText(compte, { exact: true })).toBeInTheDocument();
    if (nombre > 0) expect(screen.getByText('Outils disponibles :')).toBeInTheDocument();
  });
});
