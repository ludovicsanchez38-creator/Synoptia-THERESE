/** P-051 : une commande « action_agent » ouvre la fiche de l'agent, elle ne le lance plus directement. */
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { CommandDefinition } from '../../types/command';

vi.mock('../../services/api/commands-v3', () => ({ fetchCommandSchema: vi.fn() }));

import { useActionsStore } from '../../stores/actionsStore';
import { CommandExecutor } from './CommandExecutor';

const commandeAgent = {
  id: 'action-relance-clients', name: 'Relance clients', description: '', icon: 'Mail', category: 'produire', source: 'builtin',
  action: 'action_agent', prompt_template: null, skill_id: null, system_prompt: null, show_on_home: true, show_in_slash: false,
  sort_order: 0, image_config: null, navigate_target: null, is_editable: false,
} as unknown as CommandDefinition;

describe('CommandExecutor : agent sans paramètre (P-051)', () => {
  const ouvrirLaFicheAgent = vi.fn();
  const launchAction = vi.fn();
  beforeEach(() => {
    ouvrirLaFicheAgent.mockClear(); launchAction.mockClear();
    useActionsStore.setState({
      agents: [{ id: 'relance-clients', name: 'Relance clients', params: [] }],
      ouvrirLaFicheAgent, launchAction, openPanel: vi.fn(), selectAgent: vi.fn(),
    } as never);
  });

  it('ouvre la fiche et ne lance rien', () => {
    render(<CommandExecutor command={commandeAgent} onClose={() => {}} onPromptSelect={() => {}} onStartRFC={() => {}} />);
    expect(ouvrirLaFicheAgent).toHaveBeenCalledWith(expect.objectContaining({ id: 'relance-clients' }));
    expect(launchAction).not.toHaveBeenCalled();
  });
});
