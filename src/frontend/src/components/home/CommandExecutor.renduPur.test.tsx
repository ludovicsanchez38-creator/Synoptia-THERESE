/**
 * B-631 (persona Sophie, c4) : à l'ouverture du bloc « Produire », la console
 * affichait « Cannot update a component (HomeCommands) while rendering a
 * different component (CommandExecutor) ». L'exécution d'une commande était
 * déclenchée pendant le rendu, et une commande `prompt` remonte aussitôt
 * `onPromptSelect` puis `onClose` : deux setState du parent pendant le rendu
 * de l'enfant. Le déclenchement doit rester immédiat (avant la peinture), mais
 * hors du rendu.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { CommandDefinition } from '../../types/command';

vi.mock('../../services/api/commands-v3', () => ({ fetchCommandSchema: vi.fn() }));

import { CommandExecutor } from './CommandExecutor';

const commandePrompt: CommandDefinition = {
  id: 'prompt-relance',
  name: 'Relancer un client',
  description: 'Prépare une relance',
  icon: 'Mail',
  category: 'produire',
  source: 'builtin',
  action: 'prompt',
  prompt_template: 'Rédige une relance courtoise',
  skill_id: null,
  system_prompt: null,
  show_on_home: true,
  show_in_slash: true,
  sort_order: 0,
  image_config: null,
  navigate_target: null,
  is_editable: false,
} as unknown as CommandDefinition;

function Parent() {
  const [ouvert, setOuvert] = useState(true);
  const [prompt, setPrompt] = useState('');
  return ouvert ? (
    <CommandExecutor
      command={commandePrompt}
      onClose={() => setOuvert(false)}
      onPromptSelect={setPrompt}
      onStartRFC={() => {}}
    />
  ) : (
    <p>Fermé avec : {prompt}</p>
  );
}

function ParentQuiSeRerend({ onPromptSelect }: { onPromptSelect: (p: string) => void }) {
  const [compteur, setCompteur] = useState(0);
  return (
    <>
      <button type="button" onClick={() => setCompteur((c) => c + 1)}>Rerendre {compteur}</button>
      <CommandExecutor command={commandePrompt} onClose={() => {}} onPromptSelect={onPromptSelect} onStartRFC={() => {}} />
    </>
  );
}

describe('B-427 : une commande ne s’exécute qu’une fois tant qu’elle reste sélectionnée', () => {
  it('un second rendu du parent ne rejoue pas la commande', async () => {
    const onPromptSelect = vi.fn();
    render(<ParentQuiSeRerend onPromptSelect={onPromptSelect} />);
    await waitFor(() => expect(onPromptSelect).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: /Rerendre/ }));
    fireEvent.click(screen.getByRole('button', { name: /Rerendre/ }));
    expect(screen.getByRole('button', { name: /Rerendre 2/ })).toBeInTheDocument();
    expect(onPromptSelect).toHaveBeenCalledTimes(1);
  });
});

describe('B-631 : exécuter une commande ne met pas à jour le parent pendant le rendu', () => {
  const erreurs: string[] = [];
  let espion: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    erreurs.length = 0;
    espion = vi.spyOn(console, 'error').mockImplementation((...args: unknown[]) => {
      erreurs.push(args.map(String).join(' '));
    });
  });
  afterEach(() => {
    espion.mockRestore();
  });

  it('une commande prompt remonte son gabarit et se referme, sans avertissement React', async () => {
    render(<Parent />);
    expect(await screen.findByText('Fermé avec : Rédige une relance courtoise')).toBeInTheDocument();
    const avertissements = erreurs.filter((e) => e.includes('Cannot update a component'));
    expect(avertissements).toEqual([]);
  });
});
