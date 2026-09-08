/**
 * B-641 (persona Nadia, c4) : ⌘+⇧+K est annoncé « Katia - nouvelle tâche »
 * mais ouvrait seulement l'Atelier, focus resté sur BODY, comme ⌘+⇧+A.
 * `openPanel({ focusComposer: true })` ouvre l'onglet Chat et pose le focus
 * dans le composeur.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  streamAgentRequest: vi.fn(),
  cancelTask: vi.fn(),
  getAgentConfig: vi.fn().mockResolvedValue({ source_path: '/tmp/depot', available_models: [] }),
}));

import { useAtelierStore } from '../../stores/atelierStore';
import { AtelierPanel } from './AtelierPanel';

describe('B-641 : ouvrir l’Atelier pour une nouvelle tâche pose le focus dans le composeur', () => {
  beforeEach(() => {
    useAtelierStore.setState({ isOpen: false, activeView: 'agents', messages: [], isStreaming: false });
  });

  it('openPanel({ focusComposer: true }) bascule sur Chat et focalise la zone de saisie', async () => {
    render(<AtelierPanel />);
    useAtelierStore.getState().openPanel({ focusComposer: true });

    const champ = await screen.findByLabelText('Message à l’agent');
    await waitFor(() => expect(document.activeElement).toBe(champ));
    expect(useAtelierStore.getState().activeView).toBe('chat');
  });

  it('openPanel() sans option ne vole pas le focus', async () => {
    useAtelierStore.setState({ activeView: 'chat' });
    render(<AtelierPanel />);
    useAtelierStore.getState().openPanel();
    const champ = await screen.findByLabelText('Message à l’agent');
    expect(document.activeElement).not.toBe(champ);
  });
});
