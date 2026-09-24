/**
 * B-1176 : textes en français accentué dans l'historique du Board et les catégories de connecteurs.
 *
 * (a) Historique du Board : la confiance d'une décision est rendue brute
 *     (« Confiance high »). Attendu écrit dans la même fonctionnalité :
 *     SynthesisCard.tsx:10-29 traduit high/medium/low en « Consensus élevé /
 *     moyen / faible ».
 * (b) Paramètres > Connecteurs > Presets : catégories « Productivite » et
 *     « Avance ». Attendu : français accentué (B-650, fixed, « tout le reste
 *     de l'application est accentué » ; l'onglet Paramètres dit déjà « Avancé »,
 *     SettingsModal.tsx:49).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers } from '../lib/escapeStack';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(),
  listBoardDecisions: vi.fn(),
  getBoardDecision: vi.fn(),
  deleteBoardDecision: vi.fn(),
  listAdvisors: vi.fn().mockResolvedValue([]),
  getOllamaStatus: vi.fn().mockResolvedValue({ available: false, base_url: '', models: [], error: null }),
  listMCPServers: vi.fn().mockResolvedValue([]),
  listMCPPresets: vi.fn(),
  getMCPStatus: vi.fn().mockResolvedValue({ total_servers: 0, running_servers: 0, total_tools: 0 }),
  checkMCPPresetRequirements: vi.fn().mockResolvedValue({ all_satisfied: true, commands: {} }),
  installMCPPreset: vi.fn(),
}));

vi.mock('../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...apiMocks,
}));
vi.mock('../lib/consent', () => ({ hasCloudConsent: () => true }));

import { BoardPanel } from './board/BoardPanel';
import { ToolsPanel } from './settings/ToolsPanel';

describe('B-1176 (a) : historique du Board, confiance en français', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listBoardDecisions.mockResolvedValue([
      { id: 'd1', question: 'Faut-il recruter un alternant ?', recommendation: 'Oui', confidence: 'high', created_at: '2026-09-20T10:00:00Z' },
      { id: 'd2', question: 'Faut-il ouvrir une boutique ?', recommendation: 'Non', confidence: 'medium', created_at: '2026-09-21T10:00:00Z' },
      { id: 'd3', question: 'Faut-il lever des fonds ?', recommendation: 'Plus tard', confidence: 'low', created_at: '2026-09-22T10:00:00Z' },
    ]);
  });

  it('n’affiche pas « Confiance high/medium/low »', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));
    await screen.findByText('Faut-il recruter un alternant ?');
    const libelles = screen.getAllByText(/^Confiance /).map((n) => n.textContent);
    expect(libelles).toEqual(['Confiance élevée', 'Confiance moyenne', 'Confiance faible']);
  });
});

describe('B-1176 (b) : catégories de presets accentuées', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    apiMocks.listMCPPresets.mockResolvedValue([
      { id: 'notion', name: 'Notion', description: 'Pages et bases', category: 'productivite', command: 'npx', args: [] },
      { id: 'playwright', name: 'Playwright', description: 'Navigateur', category: 'avance', command: 'npx', args: [] },
      { id: 'brave', name: 'Brave', description: 'Recherche web', category: 'recherche', command: 'npx', args: [] },
      { id: 'hubspot', name: 'HubSpot', description: 'Contacts et affaires', category: 'crm', command: 'npx', args: [] },
    ]);
  });

  it('écrit « Productivité » et « Avancé »', async () => {
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Presets/ }));
    await screen.findByText('Recherche');
    const entetes = Array.from(document.querySelectorAll('button[aria-controls^="mcp-preset-category-"]'))
      .map((b) => b.textContent?.trim());
    expect(entetes).toEqual(['Productivité', 'Recherche', 'CRM & Ventes', 'Avancé']);
  });

  it('B-1214 : chercher « Avancé » tel qu’affiché trouve la catégorie', async () => {
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Presets/ }));
    await screen.findByText('Recherche');
    fireEvent.change(screen.getByRole('textbox', { name: 'Rechercher un preset MCP' }), { target: { value: 'Avancé' } });
    const entetes = Array.from(document.querySelectorAll('button[aria-controls^="mcp-preset-category-"]'))
      .map((b) => b.textContent?.trim());
    expect(entetes).toEqual(['Avancé']);
  });

  it('B-1228 : chercher « Ventes » tel qu’affiché trouve la catégorie « CRM & Ventes »', async () => {
    render(<ToolsPanel onError={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Presets/ }));
    await screen.findByText('Recherche');
    fireEvent.change(screen.getByRole('textbox', { name: 'Rechercher un preset MCP' }), { target: { value: 'Ventes' } });
    const entetes = Array.from(document.querySelectorAll('button[aria-controls^="mcp-preset-category-"]'))
      .map((b) => b.textContent?.trim());
    expect(entetes).toEqual(['CRM & Ventes']);
  });
});
