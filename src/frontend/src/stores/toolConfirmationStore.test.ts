import { describe, it, expect, beforeEach } from 'vitest';
import { useToolConfirmationStore } from './toolConfirmationStore';

const conf = (id: string) => ({
  confirmation_id: id,
  tool_name: 'send_email',
  arguments: { to: 'x@y.fr', subject: 'S', body: 'B' },
});

describe('toolConfirmationStore (US-002)', () => {
  beforeEach(() => useToolConfirmationStore.setState({ pending: [] }));

  it('ajoute une confirmation en attente', () => {
    useToolConfirmationStore.getState().add(conf('a'));
    expect(useToolConfirmationStore.getState().pending).toHaveLength(1);
  });

  it('ignore un doublon (même confirmation_id)', () => {
    useToolConfirmationStore.getState().add(conf('a'));
    useToolConfirmationStore.getState().add(conf('a'));
    expect(useToolConfirmationStore.getState().pending).toHaveLength(1);
  });

  it('retire une confirmation par son id', () => {
    useToolConfirmationStore.getState().add(conf('a'));
    useToolConfirmationStore.getState().add(conf('b'));
    useToolConfirmationStore.getState().remove('a');
    const ids = useToolConfirmationStore.getState().pending.map((p) => p.confirmation_id);
    expect(ids).toEqual(['b']);
  });
});
