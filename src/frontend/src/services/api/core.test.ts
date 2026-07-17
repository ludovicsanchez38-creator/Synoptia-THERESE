/**
 * Revue 0.40 : apiFetch appelait fetch() nu - une requête bloquée (backend
 * occupé, port mort) figeait l'écran sans limite. Un délai maximal commun
 * s'applique désormais, débrayable (timeoutMs: null) pour les flux SSE, les
 * appels LLM potentiellement longs et les transferts de fichiers.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiFetch, API_TIMEOUT_MS } from './core';

describe('apiFetch - délai maximal commun', () => {
  const realFetch = global.fetch;
  let captured: RequestInit | undefined;

  beforeEach(() => {
    captured = undefined;
    global.fetch = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      captured = init;
      return new Response('{}');
    }) as typeof fetch;
  });

  afterEach(() => {
    global.fetch = realFetch;
  });

  it('le défaut est de 30 secondes', () => {
    expect(API_TIMEOUT_MS).toBe(30_000);
  });

  it('attache par défaut un signal d’expiration', async () => {
    await apiFetch('http://localhost/x');
    expect(captured?.signal).toBeInstanceOf(AbortSignal);
    expect(captured?.signal?.aborted).toBe(false);
  });

  it('le signal expire réellement après timeoutMs', async () => {
    let heldSignal: AbortSignal | undefined;
    global.fetch = vi.fn((_url: RequestInfo | URL, init?: RequestInit) => {
      heldSignal = init?.signal ?? undefined;
      // Requête qui ne répond jamais : seul le délai peut la couper.
      return new Promise<Response>(() => {});
    }) as typeof fetch;

    void apiFetch('http://localhost/x', { timeoutMs: 20 }).catch(() => {});
    expect(heldSignal?.aborted).toBe(false);
    await new Promise((r) => setTimeout(r, 80));
    expect(heldSignal?.aborted).toBe(true);
  });

  it('timeoutMs: null = aucun délai (flux SSE, LLM longs, transferts)', async () => {
    await apiFetch('http://localhost/x', { timeoutMs: null });
    expect(captured?.signal ?? null).toBeNull();
  });

  it('l’annulation de l’appelant reste effective en plus du délai', async () => {
    const controller = new AbortController();
    await apiFetch('http://localhost/x', { signal: controller.signal, timeoutMs: 10_000 });
    const signal = captured?.signal;
    expect(signal?.aborted).toBe(false);
    controller.abort();
    expect(signal?.aborted).toBe(true);
  });

  it('un appelant déjà annulé part annulé', async () => {
    const controller = new AbortController();
    controller.abort();
    await apiFetch('http://localhost/x', { signal: controller.signal });
    expect(captured?.signal?.aborted).toBe(true);
  });
});
