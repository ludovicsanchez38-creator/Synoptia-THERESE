/**
 * P-113 (persona Claire, cycle 13) : le vocabulaire de la mise en route était
 * celui d'un développeur (« provider IA », « Multi-LLM », « tokens »,
 * « co-développé avec Cursor », « Sonar », « coding », « tools »,
 * « ollama / gemma4-tia:latest », « Moteur actif 8ms »). Chacun de ces mots fait
 * douter une utilisatrice qui n'est pas technicienne.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ close: vi.fn(), minimize: vi.fn(), toggleMaximize: vi.fn() }),
}));

import { FOURNISSEURS } from '../../lib/catalogueModeles';
import { useStatusStore } from '../../stores/statusStore';
import { ConnectionStatus } from '../ui/ConnectionStatus';
import { SecurityStep } from './SecurityStep';
import { WelcomeStep } from './WelcomeStep';

const JARGON = /\b(provider|multi-llm|tokens?|tools|coding|sonar|cursor)\b/i;

describe('P-113 : une mise en route sans jargon', () => {
  it('l’accueil de l’assistant ne parle ni de provider ni de Multi-LLM', () => {
    const { container } = render(<WelcomeStep onNext={vi.fn()} />);
    expect(container.textContent).not.toMatch(JARGON);
  });

  it('l’étape Sécurité parle d’outils, pas de tools', () => {
    const { container } = render(<SecurityStep provider="ollama" onNext={vi.fn()} onBack={vi.fn()} />);
    expect(container.textContent).not.toMatch(JARGON);
  });

  it('aucune description de service d’IA n’emploie de jargon', () => {
    const fautives = FOURNISSEURS.filter((f) => JARGON.test(f.description)).map((f) => `${f.id} : ${f.description}`);
    expect(fautives).toEqual([]);
  });

  it('l’en-tête dit que le moteur tourne, sans afficher de millisecondes', () => {
    useStatusStore.setState({ connectionState: 'connected', latency: 8 } as never);
    const { container } = render(<ConnectionStatus />);
    expect(container.textContent).not.toMatch(/\d+\s*ms\b/);
    expect(screen.getByText('Moteur actif').closest('[title]')).toHaveAttribute('title', expect.stringMatching(/8 ms/));
  });
});
