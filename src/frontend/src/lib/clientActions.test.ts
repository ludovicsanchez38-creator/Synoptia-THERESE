/**
 * Actions déterministes - tranche 1a : exécution côté client de l'événement
 * `client_action` émis par le backend pour un message-action pur
 * ({action: ouvrir email} -> navigation locale, zéro LLM).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { handleClientActionChunk } from './clientActions';
import { runAction } from './actionRegistry';

vi.mock('./actionRegistry', async () => {
  const actual = await vi.importActual<typeof import('./actionRegistry')>('./actionRegistry');
  return { ...actual, runAction: vi.fn(() => true) };
});

const mockedRun = vi.mocked(runAction);

describe('handleClientActionChunk', () => {
  beforeEach(() => mockedRun.mockClear());

  it('exécute une navigation via le registre d\'actions', () => {
    const handled = handleClientActionChunk({
      type: 'client_action',
      content: '',
      client_action: { action: 'navigate', action_id: 'email.open', target: 'email' },
    } as never);
    expect(handled).toBe(true);
    expect(mockedRun).toHaveBeenCalledWith('email.open');
  });

  it('ignore un chunk sans client_action exploitable', () => {
    expect(handleClientActionChunk({ type: 'client_action', content: '' } as never)).toBe(false);
    expect(
      handleClientActionChunk({
        type: 'client_action',
        content: '',
        client_action: { action: 'autre_chose', action_id: 'email.open' },
      } as never)
    ).toBe(false);
    expect(mockedRun).not.toHaveBeenCalled();
  });
});
