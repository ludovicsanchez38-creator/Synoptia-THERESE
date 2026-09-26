/**
 * B-1621 (décision de Ludo, 26/09) : en mode démo, supprimer, anonymiser ou
 * déplacer agissait sur la vraie fiche alors que la confirmation montrait le
 * pseudonyme. Ces gestes sont bloqués en démo, et la raison se dit.
 */
import { beforeEach, describe, expect, it } from 'vitest';

import { gesteBloqueEnDemo, MESSAGE_GESTE_EN_DEMO } from './gesteEnDemo';
import { useDemoStore } from '../stores/demoStore';
import { useStatusStore } from '../stores/statusStore';

describe('B-1621 : gestes destructifs en démo', () => {
  beforeEach(() => {
    useStatusStore.setState({ notifications: [] } as never);
  });

  it('en démo, le geste est bloqué et la raison se dit', () => {
    useDemoStore.setState({ enabled: true } as never);
    expect(gesteBloqueEnDemo()).toBe(true);
    const notes = useStatusStore.getState().notifications;
    expect(notes.at(-1)?.message).toBe(MESSAGE_GESTE_EN_DEMO);
  });

  it('hors démo, le geste passe sans rien dire', () => {
    useDemoStore.setState({ enabled: false } as never);
    expect(gesteBloqueEnDemo()).toBe(false);
    expect(useStatusStore.getState().notifications).toHaveLength(0);
  });
});
