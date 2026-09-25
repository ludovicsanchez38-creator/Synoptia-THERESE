/**
 * B-1459 (recette P-146, lot 4, KO-1) : après « Confirmer » sur la carte de
 * création d'un contact, le fil annonçait « Délai de 30000 ms dépassé » alors
 * que la fiche existait : l'action attendait son indexation vectorielle, près
 * d'une minute sous la charge du modèle local. Une action confirmée peut
 * durer (document, indexation, envoi) : elle n'a plus de délai client.
 */
import { describe, expect, it, vi } from 'vitest';

const { request } = vi.hoisted(() => ({ request: vi.fn() }));
vi.mock('./core', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./core')>()),
  request,
}));

import { confirmTool } from './chat';

describe('B-1459 : une action confirmée n’a pas de délai client', () => {
  it('confirmTool passe timeoutMs: null', async () => {
    request.mockResolvedValue({ status: 'executed', tool_name: 'create_contact', result: 'ok' });
    await confirmTool('c-1', true);
    expect(request).toHaveBeenCalledWith('/api/chat/confirm-tool', expect.objectContaining({ timeoutMs: null }));
  });
});
