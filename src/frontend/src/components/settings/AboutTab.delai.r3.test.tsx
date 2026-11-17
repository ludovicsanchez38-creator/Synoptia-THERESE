import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useBackendStore } from '../../hooks/useBackend';
import { API_TIMEOUT_MS } from '../../services/api/core';
import { AboutTab } from './AboutTab';

const moteur = { version: '0.83.0-alpha.1', status: 'healthy' };

describe('R3-2 : la lecture complète de la version est bornée', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useBackendStore.getState().reset();
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it.each([
    ['montage', 'résolution'],
    ['clic partagé', 'résolution'],
    ['clic partagé', 'rejet'],
  ])('libère la lecture au %s malgré un corps bloqué et ignore son issue tardive (%s)', async (origine, issue) => {
    let finirAncienne!: (valeur: typeof moteur) => void;
    let rejeterAncienne!: (erreur: Error) => void;
    let finirNouvelle!: (valeur: typeof moteur) => void;
    const corpsAncien = new Promise<typeof moteur>((resolve, reject) => {
      finirAncienne = resolve;
      rejeterAncienne = reject;
    });
    const corpsNouveau = new Promise<typeof moteur>((resolve) => { finirNouvelle = resolve; });
    const lireCorps = vi.fn().mockReturnValueOnce(corpsAncien).mockReturnValueOnce(corpsNouveau);
    const signaux: (AbortSignal | null | undefined)[] = [];
    const requetes = vi.fn<typeof fetch>(async (url, options) => {
      if (String(url).endsWith('/health')) {
        signaux.push(options?.signal);
        // Les en-têtes arrivent ; même une lecture ignorant l'annulation reste bornée.
        return { ok: true, status: 200, json: lireCorps } as unknown as Response;
      }
      if (String(url).startsWith('https://api.github.com/repos/')) {
        return new Response(JSON.stringify([{ tag_name: 'v0.83.0-alpha.2', assets: [] }]));
      }
      throw new Error('Requête non simulée');
    });
    vi.stubGlobal('fetch', requetes);

    await act(async () => { render(<AboutTab />); });
    expect(lireCorps).toHaveBeenCalledTimes(1);
    if (origine === 'clic partagé') {
      fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
      expect(screen.getByRole('button', { name: 'Vérification...' })).toBeDisabled();
    }
    await act(async () => { await vi.advanceTimersByTimeAsync(API_TIMEOUT_MS); });
    expect(screen.getByRole('alert')).toHaveTextContent('Impossible de lire la version installée');
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE manuellement' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Vérifier les mises à jour' })).toBeEnabled();
    expect(signaux[0]?.aborted).toBe(true);
    expect(requetes).toHaveBeenCalledTimes(1);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
    });
    expect(lireCorps).toHaveBeenCalledTimes(2);
    await act(async () => {
      if (issue === 'résolution') finirAncienne({ ...moteur, version: '0.1.0-alpha' });
      else rejeterAncienne(new Error('Ancien corps interrompu'));
    });
    expect(useBackendStore.getState().version).toBeNull();
    expect(screen.getByRole('button', { name: 'Vérification...' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Lecture de la version installée en cours...');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(requetes).toHaveBeenCalledTimes(2);

    await act(async () => { finirNouvelle(moteur); });
    expect(screen.getByText('Nouvelle version disponible : v0.83.0-alpha.2')).toBeInTheDocument();
    expect(useBackendStore.getState().version).toBe(moteur.version);
    expect(requetes).toHaveBeenCalledTimes(3);
    expect(signaux[1]?.aborted).toBe(false);
  });
});
