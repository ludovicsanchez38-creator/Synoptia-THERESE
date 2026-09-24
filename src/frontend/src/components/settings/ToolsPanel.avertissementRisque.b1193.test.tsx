/**
 * B-1193 : l'avertissement de risque d'un connecteur MCP est lisible avant qu'un clic ne l'installe.
 *
 * Le moteur décrit chaque preset à risque par `risk_level` et une phrase
 * `risk_warning` (routers/mcp.py : Filesystem « medium », Playwright « high »,
 * sans clé requise). Attendu : cette phrase atteint l'utilisateur avant
 * qu'un clic n'installe et ne démarre le connecteur. On mesure où elle est
 * rendue, le nom accessible de la carte, et ce que fait un clic.
 *
 * Le rendu de la carte est aussi écrit dans repro-c13b/g1/b1193-carte.html :
 * repro-c13b/g1/b1193_hit_test.mjs le charge dans Chromium avec la CSS
 * compilée par Vite pour mesurer le hit-test (JSDOM n'en fait pas).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const AVERTISSEMENT_PLAYWRIGHT =
  'Peut exécuter des actions dans un navigateur (cliquer, remplir des formulaires, télécharger)';
const AVERTISSEMENT_FILESYSTEM = 'Peut lire et modifier tous les fichiers du dossier de travail';
const AVERTISSEMENT_STRIPE =
  'Accès aux paiements et données financières. Peut créer des factures et des liens de paiement.';

const apiMocks = vi.hoisted(() => ({
  listMCPServers: vi.fn().mockResolvedValue([]),
  listMCPPresets: vi.fn(),
  getMCPStatus: vi.fn().mockResolvedValue({ total_servers: 0, running_servers: 0, total_tools: 0 }),
  checkMCPPresetRequirements: vi.fn().mockResolvedValue({ all_satisfied: true, commands: {} }),
  installMCPPreset: vi.fn(),
  startMCPServer: vi.fn(),
}));

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...apiMocks,
}));

import { ToolsPanel } from './ToolsPanel';

const PRESETS = [
  {
    id: 'filesystem', name: 'Filesystem', description: 'Lecture, écriture, copie de fichiers locaux',
    category: 'essentiels', risk_level: 'medium', risk_warning: AVERTISSEMENT_FILESYSTEM,
    command: 'npx', args: [],
  },
  {
    id: 'stripe', name: 'Stripe', description: 'Paiements, clients, factures, liens de paiement',
    category: 'finance', popular: true, url: 'https://stripe.com', risk_level: 'high',
    risk_warning: AVERTISSEMENT_STRIPE, command: 'npx', args: [], env_required: ['STRIPE_API_KEY'],
  },
  {
    id: 'playwright', name: 'Playwright', description: 'Automatisation navigateur web (formulaires, extraction)',
    category: 'avance', risk_level: 'high', risk_warning: AVERTISSEMENT_PLAYWRIGHT,
    command: 'npx', args: [],
  },
];

async function ouvrirPresets() {
  render(<ToolsPanel onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: /Presets/ }));
  await screen.findByRole('button', { name: 'Installer Filesystem' });
  // La catégorie « Avance » est repliée par défaut : on la déplie.
  fireEvent.click(document.querySelector('button[aria-controls="mcp-preset-category-avance"]') as HTMLElement);
  return screen.findByRole('button', { name: 'Installer Playwright' });
}

describe('B-1193 : avertissement de risque des presets MCP', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    apiMocks.listMCPPresets.mockResolvedValue(PRESETS);
    apiMocks.installMCPPreset.mockImplementation(async (id: string) => ({
      id: `srv-${id}`, name: id, command: 'npx', args: [], status: 'running', env: {}, tools: [],
    }));
  });

  it('l’avertissement « Élevé » de Playwright est perceptible avant que le clic n’installe', async () => {
    const carte = await ouvrirPresets();
    // Avant le clic : la phrase de risque est affichée en texte et décrit la carte.
    const texte = screen.getByText(AVERTISSEMENT_PLAYWRIGHT);
    expect({
      avertissementEnTexte: true,
      decritLaCarte: (carte.getAttribute('aria-describedby') ?? '').split(' ').includes(texte.id),
    }).toEqual({ avertissementEnTexte: true, decritLaCarte: true });
    fireEvent.click(carte);
    await waitFor(() => expect(apiMocks.installMCPPreset).toHaveBeenCalled());
  });

  it('même mesure pour Filesystem (« Moyen », pas de clé requise)', async () => {
    await ouvrirPresets();
    const carte = screen.getByRole('button', { name: 'Installer Filesystem' });
    const etat = {
      nomAccessible: carte.getAttribute('aria-label'),
      avertissementEnTexte: screen.queryByText(AVERTISSEMENT_FILESYSTEM) !== null,
    };
    fireEvent.click(carte);
    await waitFor(() => expect(apiMocks.installMCPPreset).toHaveBeenCalled());
    expect({
      ...etat,
      installAppeleAvec: apiMocks.installMCPPreset.mock.calls[0],
      dialogue: screen.queryByRole('dialog') !== null,
    }).toMatchObject({ avertissementEnTexte: true });
  });

  it('Stripe (clé requise) : la modale des variables devrait porter l’avertissement', async () => {
    await ouvrirPresets();
    fireEvent.click(screen.getByRole('button', { name: 'Installer Stripe' }));
    const modale = await screen.findByRole('dialog');
    expect({
      installAppele: apiMocks.installMCPPreset.mock.calls.length,
      avertissementDansLaModale: (modale.textContent ?? '').includes(AVERTISSEMENT_STRIPE),
    }).toEqual({ installAppele: 0, avertissementDansLaModale: true });
  });
});
