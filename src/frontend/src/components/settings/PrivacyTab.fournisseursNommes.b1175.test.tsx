/**
 * B-1175 : la liste des accords nomme le fournisseur, jamais sa clé brute.
 *
 * L'accord « Ollama Cloud » est demandé au chat sous le libellé
 * libelleDuFournisseur('ollama-cloud') = « Ollama Cloud (ollama.com) »
 * (libellesFournisseurs.ts:31-35, B-1158). La liste des accords de
 * Paramètres > Confidentialité humanise déjà la clé « board »
 * (PrivacyTab.tsx:437-439) : l'intention d'afficher un libellé existe.
 * On mesure ce que la liste affiche pour l'accord « ollama-cloud ».
 */
import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { grantCloudConsent } from '../../lib/consent';
import { libelleDuFournisseur } from '../../lib/libellesFournisseurs';
import { PrivacyTab } from './PrivacyTab';

vi.mock('./VoiceLocalSection', () => ({
  VoiceLocalSection: () => <div>Voix locale</div>,
}));
vi.mock('../../services/api/rgpd', () => ({
  getPurgeSettings: vi.fn().mockResolvedValue({ enabled: true, months: 36 }),
  updatePurgeSettings: vi.fn().mockResolvedValue(undefined),
}));
vi.mock('../../services/api/data', () => ({
  downloadAllData: vi.fn(),
  listBackups: vi.fn().mockResolvedValue([]),
  createBackup: vi.fn(),
  restoreBackup: vi.fn(),
  deleteBackup: vi.fn(),
  deleteAllData: vi.fn(),
}));

function ligneDAccord(): string {
  const bouton = screen.getAllByRole('button', { name: 'Révoquer' })[0];
  return bouton.closest('li')?.textContent ?? '';
}

describe('B-1175 : Confidentialité nomme l’accord Ollama Cloud', () => {
  beforeEach(() => {
    // Le setup global mocke localStorage sans persistance (comme PrivacyTab.test.tsx).
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => { store[k] = v; },
      removeItem: (k: string) => { delete store[k]; },
      clear: () => { for (const k of Object.keys(store)) delete store[k]; },
    });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('affiche « Ollama Cloud (ollama.com) » et pas la clé brute « ollama-cloud »', async () => {
    grantCloudConsent('llm', 'ollama-cloud', ['message saisi'], '2026-09-24T10:00:00.000Z');
    render(<PrivacyTab />);
    await screen.findAllByRole('button', { name: 'Révoquer' });
    const ligne = ligneDAccord();
    const etat = {
      libelleDeLaDemande: libelleDuFournisseur('ollama-cloud'),
      ligneContientLeLibelle: ligne.includes('Ollama Cloud (ollama.com)'),
      ligneContientLaCleBrute: /\bollama-cloud\b/.test(ligne),
      ligne,
    };
    expect(etat).toEqual({
      libelleDeLaDemande: 'Ollama Cloud (ollama.com)',
      ligneContientLeLibelle: true,
      ligneContientLaCleBrute: false,
      ligne: expect.stringContaining('Ollama Cloud (ollama.com)'),
    });
  });

  it('patron préexistant (même cause) : « openai » devrait se lire « OpenAI »', async () => {
    grantCloudConsent('llm', 'openai', ['message saisi'], '2026-09-24T10:00:00.000Z');
    render(<PrivacyTab />);
    await screen.findAllByRole('button', { name: 'Révoquer' });
    const ligne = ligneDAccord();
    expect({ libelle: libelleDuFournisseur('openai'), ligne })
      .toEqual({ libelle: 'OpenAI', ligne: expect.stringContaining('OpenAI') });
  });

  it('témoin : la clé « board » est déjà humanisée par la même boucle', async () => {
    grantCloudConsent('llm', 'board', ['question'], '2026-09-24T10:00:00.000Z');
    render(<PrivacyTab />);
    await screen.findAllByRole('button', { name: 'Révoquer' });
    expect(ligneDAccord()).toContain('Board (plusieurs fournisseurs IA)');
  });

  it('B-1216 : un accord de génération d’images nomme le moteur', async () => {
    grantCloudConsent('images', 'fal-flux-pro', ['prompt'], '2026-09-24T10:00:00.000Z');
    render(<PrivacyTab />);
    await screen.findAllByRole('button', { name: 'Révoquer' });
    const ligne = ligneDAccord();
    expect({ nomme: ligne.includes('Fal Flux Pro'), cleBrute: ligne.includes('fal-flux-pro') })
      .toEqual({ nomme: true, cleBrute: false });
  });

  it('B-1217 : l’encadré ne promet pas qu’un modèle Ollama Cloud reste local', async () => {
    render(<PrivacyTab />);
    const encadre = (await screen.findByText('Ce qui peut sortir de ta machine')).parentElement?.textContent ?? '';
    expect(encadre).toContain('Ollama Cloud');
  });
});
