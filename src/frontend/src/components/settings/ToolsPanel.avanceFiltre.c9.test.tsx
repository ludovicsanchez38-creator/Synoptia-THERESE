/**
 * B-871 (cycle 9, relecteur U4) : la catégorie « Avancé » des presets MCP est
 * repliée par défaut, et ce repli n'était qu'un état initial. Une recherche
 * saisie après le montage qui ne ramène que des presets avancés laissait un
 * en-tête replié et aucune carte : « GitHub » semblait ne pas exister.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listMCPServers: vi.fn().mockResolvedValue([]),
  listMCPPresets: vi.fn().mockResolvedValue([
    { id: 'filesystem', name: 'Fichiers locaux', description: 'Lire des fichiers', category: 'essentiels', command: 'npx', args: [], installed: false },
    { id: 'github', name: 'GitHub', description: 'Dépôts et tickets', category: 'avance', command: 'npx', args: [], installed: false },
  ]),
  getMCPStatus: vi.fn().mockResolvedValue({ total_servers: 0, running: 0, stopped: 0, error: 0 }),
  checkMCPPresetRequirements: vi.fn().mockResolvedValue({ all_satisfied: true, commands: {} }),
}));

import { ToolsPanel } from './ToolsPanel';

describe('ToolsPanel - B-871, un filtre déplie la catégorie « Avancé »', () => {
  beforeEach(() => vi.clearAllMocks());

  it('une recherche qui ne ramène qu’un preset avancé montre sa carte', async () => {
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Presets/ }));
    await screen.findByLabelText('Installer Fichiers locaux');
    expect(screen.queryByLabelText('Installer GitHub')).toBeNull();

    fireEvent.change(screen.getByLabelText('Rechercher un preset MCP'), { target: { value: 'git' } });
    expect(await screen.findByLabelText('Installer GitHub')).toBeInTheDocument();
  });
});
