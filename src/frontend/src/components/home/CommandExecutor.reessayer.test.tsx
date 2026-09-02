/**
 * B-097 : « Réessayer » ne réessayait rien.
 *
 * Mesuré au navigateur : après l'échec d'une génération de document, le clic
 * sur « Réessayer » n'émettait AUCUNE requête vers /api/skills ; le panneau
 * disparaissait, le formulaire revenait VIDE, et la saisie était perdue. Le
 * bouton signifiait en réalité « tout recommencer à la main ».
 *
 * Cause : `SkillExecutionPanel` câble le bouton sur `onRetry`, et le seul
 * appelant vivant passait `onRetry={() => setSkillState(null)}` — un effacement
 * d'état, pas une relance ; les entrées, elles, étaient déjà jetées
 * (`setDynamicSkill(null)`) avant même l'appel.
 *
 * Le test COMPTE les appels : un test qui n'observerait que l'état repasserait
 * au vert sur le défaut d'origine.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { CommandDefinition } from '../../types/command';

const executeSkill = vi.fn();
const fetchCommandSchema = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    executeSkill: (...args: unknown[]) => executeSkill(...args),
    downloadSkillFile: vi.fn(),
  };
});

vi.mock('../../services/api/commands-v3', () => ({
  fetchCommandSchema: (...args: unknown[]) => fetchCommandSchema(...args),
}));

import { CommandExecutor } from './CommandExecutor';

const commande: CommandDefinition = {
  id: 'docx-pro',
  name: 'Document Word',
  description: 'Génère un document Word',
  icon: 'file',
  category: 'produire',
  source: 'skill',
  action: 'form_then_file',
  prompt_template: '',
  skill_id: 'docx-pro',
  system_prompt: null,
  show_on_home: true,
  show_in_slash: true,
  sort_order: 0,
  image_config: null,
  navigate_target: null,
  is_editable: false,
};

const schema = {
  skill_id: 'docx-pro',
  output_type: 'file' as const,
  schema: {
    sujet: { type: 'text' as const, label: 'Sujet', required: true },
  },
};

describe('B-097 : « Réessayer » relance vraiment la génération', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchCommandSchema.mockResolvedValue(schema);
    executeSkill.mockResolvedValue({ success: false, error: 'Panne simulée' });
  });

  it('après un échec, le clic sur Réessayer rappelle executeSkill avec les MÊMES entrées', async () => {
    render(
      <CommandExecutor
        command={commande}
        onClose={() => {}}
        onPromptSelect={() => {}}
        onStartRFC={() => {}}
      />,
    );

    const champ = await screen.findByLabelText(/Sujet/);
    fireEvent.change(champ, { target: { value: 'Compte rendu de chantier Vernet' } });
    fireEvent.click(screen.getByRole('button', { name: /Générer/i }));

    await waitFor(() => expect(executeSkill).toHaveBeenCalledTimes(1));
    const premierAppel = executeSkill.mock.calls[0];

    const reessayer = await screen.findByRole('button', { name: /Réessayer/i });
    fireEvent.click(reessayer);

    // C'est le comptage qui ferme le défaut : l'ancien onRetry effaçait l'état
    // sans jamais rappeler l'API.
    await waitFor(() => expect(executeSkill).toHaveBeenCalledTimes(2));
    expect(executeSkill.mock.calls[1]).toEqual(premierAppel);

    // Et la relance ne repasse pas par le formulaire : re-charger le schéma
    // ramènerait l'écran vide dénoncé par la fiche.
    expect(fetchCommandSchema).toHaveBeenCalledTimes(1);
    expect(screen.queryByLabelText(/Sujet/)).toBeNull();
  });
});
