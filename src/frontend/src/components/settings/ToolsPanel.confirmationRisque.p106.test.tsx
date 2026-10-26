import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { MCPPreset } from '../../services/api';

const api = vi.hoisted(() => ({
  listMCPServers: vi.fn(),
  listMCPPresets: vi.fn(),
  getMCPStatus: vi.fn(),
  checkMCPPresetRequirements: vi.fn(),
  installMCPPreset: vi.fn(),
  startMCPServer: vi.fn(),
}));
vi.mock('../../services/api', async (original) => ({ ...(await original<object>()), ...api }));
import { ToolsPanel } from './ToolsPanel';

const preset: MCPPreset = {
  id: 'automate', name: 'Automate', description: 'Automatiser la navigation web.',
  category: 'essentiels', command: 'npx', args: [], installed: false,
  risk_level: 'high', risk_warning: 'Peut remplir et envoyer des formulaires sur le web.',
};

async function ouvrir(entree: MCPPreset = preset) {
  api.listMCPPresets.mockResolvedValue([entree]);
  render(<ToolsPanel onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: /Presets/ }));
  const carte = await screen.findByRole('button', { name: `Installer ${entree.name}` });
  carte.focus();
  await act(async () => { fireEvent.click(carte); });
  return carte;
}

describe('P-106 : confirmer l’installation des connecteurs à risque élevé', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    _clearEscapeHandlers();
    api.listMCPServers.mockResolvedValue([]);
    api.getMCPStatus.mockResolvedValue({ total_servers: 0, running_servers: 0, total_tools: 0 });
    api.checkMCPPresetRequirements.mockResolvedValue({ all_satisfied: true, commands: {} });
    api.installMCPPreset.mockResolvedValue({
      id: 'srv-automate', name: 'Automate', status: 'running', tools: [],
      command: 'npx', args: [], env: {}, enabled: true, error: null,
      created_at: '2026-10-26T10:00:00Z',
    });
  });

  it('le premier clic décrit les capacités et place le focus sur Annuler, sans installer', async () => {
    await ouvrir();
    const dialogue = await screen.findByRole('dialog', { name: 'Installer Automate ?' });
    expect(dialogue).toHaveAttribute('aria-modal', 'true');
    expect(dialogue).toHaveAccessibleDescription(expect.stringContaining(preset.risk_warning!));
    expect(dialogue).toHaveTextContent(preset.description);
    expect(within(dialogue).getByRole('button', { name: 'Annuler' })).toHaveFocus();
    expect(api.installMCPPreset).not.toHaveBeenCalled();
    expect(api.startMCPServer).not.toHaveBeenCalled();
  });

  it.each(['Annuler', 'Échap'])('%s ferme sans installer et rend le focus à la carte', async (action) => {
    const carte = await ouvrir();
    const dialogue = await screen.findByRole('dialog', { name: 'Installer Automate ?' });
    if (action === 'Échap') fireEvent.keyDown(document.activeElement!, { key: 'Escape' });
    else fireEvent.click(within(dialogue).getByRole('button', { name: 'Annuler' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(carte).toHaveFocus();
    expect(api.installMCPPreset).not.toHaveBeenCalled();
    expect(api.startMCPServer).not.toHaveBeenCalled();
  });

  it('Tab et Maj+Tab restent dans la confirmation ; Installer lance une seule installation', async () => {
    await ouvrir();
    const dialogue = await screen.findByRole('dialog', { name: 'Installer Automate ?' });
    const annuler = within(dialogue).getByRole('button', { name: 'Annuler' });
    const installer = within(dialogue).getByRole('button', { name: 'Installer' });
    fireEvent.keyDown(annuler, { key: 'Tab', shiftKey: true });
    expect(installer).toHaveFocus();
    fireEvent.keyDown(installer, { key: 'Tab' });
    expect(annuler).toHaveFocus();
    // JSDOM ne produit pas le clic natif d’Entrée : on le rejoue si la touche reste libre.
    installer.focus();
    expect(fireEvent.keyDown(installer, { key: 'Enter', code: 'Enter' })).toBe(true);
    fireEvent.click(installer);
    await waitFor(() => expect(api.installMCPPreset).toHaveBeenCalledExactlyOnceWith('automate', {}));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it.each(['low', 'medium'] as const)('risque %s : le clic installe directement', async (risk_level) => {
    await ouvrir({ ...preset, risk_level });
    await waitFor(() => expect(api.installMCPPreset).toHaveBeenCalledExactlyOnceWith('automate', {}));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('un risque élevé sans phrase dédiée reste soumis à confirmation avec sa description', async () => {
    await ouvrir({ ...preset, risk_warning: undefined });
    const dialogue = await screen.findByRole('dialog', { name: 'Installer Automate ?' });
    expect(dialogue).toHaveAccessibleDescription(expect.stringContaining(preset.description));
    expect(api.installMCPPreset).not.toHaveBeenCalled();
  });

  it('la confirmation précède la saisie des paramètres requis et celle-ci peut encore être annulée', async () => {
    await ouvrir({ ...preset, env_required: ['ESPACE_TEST'] });
    const dialogue = await screen.findByRole('dialog', { name: 'Installer Automate ?' });
    expect(api.installMCPPreset).not.toHaveBeenCalled();
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Installer' }));
    const saisie = await screen.findByRole('dialog', { name: 'Configuration Automate' });
    expect(saisie.contains(document.activeElement)).toBe(true);
    expect(api.installMCPPreset).not.toHaveBeenCalled();
    fireEvent.click(within(saisie).getByRole('button', { name: 'Annuler' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(api.installMCPPreset).not.toHaveBeenCalled();
  });
});
