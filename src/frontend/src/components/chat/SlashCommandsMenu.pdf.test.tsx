/** B-1246 : les deux intentions PDF doivent rester distinctes à la sélection. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useCommandsStore } from '../../stores/commandsStore';
import type { CommandDefinition } from '../../types/command';
import { SlashCommandsMenu } from './SlashCommandsMenu';

function commande(id: string, name: string): CommandDefinition {
  return {
    id, name, description: name, icon: 'FileText', category: 'general',
    source: 'skill', action: id === 'pdf-pro' ? 'form_then_file' : 'form_then_prompt',
    prompt_template: '', skill_id: id, system_prompt: null,
    show_on_home: true, show_in_slash: true, sort_order: 100,
    image_config: null, navigate_target: null, is_editable: false,
  };
}

beforeEach(() => {
  Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
    configurable: true, value: vi.fn(),
  });
  // Le contrat de ces noms est vérifié sur le vrai registre par le test Python B-1246.
  useCommandsStore.setState({ commands: [
    commande('analyze-pdf', 'Analyser un PDF'), commande('pdf-pro', 'Générer un PDF'),
  ] });
});

afterEach(() => {
  cleanup();
  useCommandsStore.setState({ commands: [] });
});

function menu(query = '/') {
  const onSelect = vi.fn();
  render(<SlashCommandsMenu isOpen query={query} selectedIndex={0} onSelect={onSelect}
    onClose={vi.fn()} onIndexChange={vi.fn()} />);
  return onSelect;
}

describe('PDF : analyser ou générer', () => {
  it('affiche deux libellés et insère deux préfixes distincts au clic', () => {
    const onSelect = menu();
    fireEvent.click(screen.getByRole('button', { name: /\/Analyser un PDF/ }));
    fireEvent.click(screen.getByRole('button', { name: /\/Générer un PDF/ }));
    expect(onSelect.mock.calls.map(([c]) => [c.id, c.prefix])).toEqual([
      ['analyze-pdf', '/Analyser un PDF '], ['pdf-pro', '/Générer un PDF '],
    ]);
    expect(screen.queryByText('/Document PDF')).toBeNull();
  });

  it.each([
    ['/Analyser un PDF', 'Enter', 'analyze-pdf', '/Analyser un PDF '],
    ['/Générer un PDF', 'Tab', 'pdf-pro', '/Générer un PDF '],
  ])('sélectionne %s au clavier', (query, key, id, prefix) => {
    const onSelect = menu(query);
    fireEvent.keyDown(window, { key });
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id, prefix }));
  });
});
