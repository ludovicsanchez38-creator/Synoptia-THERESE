/**
 * Revue 0.40 : une panne du sidecar imposait de relancer toute l'application,
 * sans aucun message. Le bandeau suit les événements `sidecar-status` émis par
 * Rust (relances automatiques) et offre une relance manuelle après épuisement.
 */
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

type StatusPayload = { state: 'restarting' | 'failed' | 'running'; attempt: number };

const harness = vi.hoisted(() => ({
  handler: null as ((event: { payload: StatusPayload }) => void) | null,
  invoke: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn((_name: string, cb: (event: { payload: StatusPayload }) => void) => {
    harness.handler = cb;
    return Promise.resolve(() => {
      harness.handler = null;
    });
  }),
}));

vi.mock('@tauri-apps/api/core', () => ({
  invoke: harness.invoke,
}));

import { SidecarStatusBanner } from './SidecarStatusBanner';

function emit(payload: StatusPayload) {
  act(() => harness.handler?.({ payload }));
}

describe('SidecarStatusBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    harness.handler = null;
    // @ts-expect-error simulation contexte Tauri
    window.__TAURI__ = {};
  });

  it('ne rend rien tant que le moteur local vit sa vie', async () => {
    const { container } = render(<SidecarStatusBanner />);
    await waitFor(() => expect(harness.handler).not.toBeNull());
    expect(container.firstChild).toBeNull();
  });

  it('annonce les relances automatiques avec la tentative en cours', async () => {
    render(<SidecarStatusBanner />);
    await waitFor(() => expect(harness.handler).not.toBeNull());

    emit({ state: 'restarting', attempt: 2 });

    expect(screen.getByRole('status')).toHaveTextContent('Le moteur local redémarre');
    expect(screen.getByRole('status')).toHaveTextContent('tentative 2/3');
  });

  it('après échec des 3 relances, propose « Relancer le moteur local »', async () => {
    render(<SidecarStatusBanner />);
    await waitFor(() => expect(harness.handler).not.toBeNull());

    emit({ state: 'failed', attempt: 3 });
    expect(screen.getByRole('alert')).toHaveTextContent('moteur local ne répond plus');

    fireEvent.click(screen.getByRole('button', { name: 'Relancer le moteur local' }));
    await waitFor(() => expect(harness.invoke).toHaveBeenCalledWith('restart_backend'));
    // Le bandeau repasse en mode « relance en cours » sans attendre l'événement Rust.
    expect(screen.getByRole('status')).toHaveTextContent('Le moteur local redémarre');
  });

  it('disparaît quand le moteur est reparti', async () => {
    const { container } = render(<SidecarStatusBanner />);
    await waitFor(() => expect(harness.handler).not.toBeNull());

    emit({ state: 'restarting', attempt: 1 });
    emit({ state: 'running', attempt: 0 });

    expect(container.firstChild).toBeNull();
  });
});
