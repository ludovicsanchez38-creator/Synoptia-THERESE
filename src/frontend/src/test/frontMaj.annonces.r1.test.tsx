import { act, fireEvent, isInaccessible, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api', () => ({ streamMessage: vi.fn(), checkHealth: vi.fn() }));
import { streamMessage } from '../services/api';
import { useBackendStore } from '../hooks/useBackend';
import { RFCChat } from '../components/rfc/RFCChat';
import { AboutTab } from '../components/settings/AboutTab';

Element.prototype.scrollTo = vi.fn();

describe('R1-7 : les régions live précèdent leur contenu', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('mini-chat : conserve la région vide, puis annonce le début du flux dans le même nœud', async () => {
    let terminer!: () => void;
    const attente = new Promise<void>((resolve) => { terminer = resolve; });
    vi.mocked(streamMessage).mockImplementation(async function* () {
      await attente;
      yield { type: 'text', content: 'Réponse terminée' };
      yield { type: 'done', content: '', message_id: 'source' };
    });
    render(<RFCChat systemPrompt="x" placeholder="Brief" onConversationUpdate={vi.fn()} />);
    try {
      const region = screen.getByRole('status');
      expect(region).toBeEmptyDOMElement();
      expect(isInaccessible(region)).toBe(false);
      fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Un brief' } });
      fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
      expect(screen.getByRole('status')).toBe(region);
      expect(region).toHaveTextContent('THÉRÈSE réfléchit...');
      await act(async () => terminer());
      expect(screen.getByRole('status')).toBe(region);
      expect(region).toBeEmptyDOMElement();
    } finally {
      await act(async () => terminer());
    }
  });

  it('à propos : la région vide est accessible avant le clic, avec la sémantique CSS de production', async () => {
    // Vitest ne compile pas Tailwind : appliquer la règle de la classe en cause.
    const style = document.createElement('style');
    style.textContent = String.raw`.empty\:hidden:empty { display: none; }`;
    document.head.appendChild(style);
    useBackendStore.setState({ version: '0.83.0' });
    let terminer!: (value: unknown) => void;
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise((resolve) => { terminer = resolve; })));
    try {
      render(<AboutTab />);
      const region = screen.getByRole('status', { hidden: true });
      expect(isInaccessible(region)).toBe(false);
      expect(region).toBeEmptyDOMElement();
      fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
      expect(screen.getByRole('status')).toBe(region);
      expect(region).toHaveTextContent(/Vérification.*en cours/);
      await act(async () => terminer({ ok: true, json: async () => [{ tag_name: 'v0.83.0', assets: [] }] }));
      expect(screen.getByRole('status')).toBe(region);
      expect(region).toHaveTextContent('THÉRÈSE est à jour');
    } finally {
      style.remove();
      await act(async () => terminer({ ok: true, json: async () => [] }));
    }
  });
});
