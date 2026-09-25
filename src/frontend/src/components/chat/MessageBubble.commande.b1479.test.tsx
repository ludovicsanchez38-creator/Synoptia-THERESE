import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

const { downloadSkillFileMock, fetchImageObjectUrlMock } = vi.hoisted(() => ({
  downloadSkillFileMock: vi.fn(),
  fetchImageObjectUrlMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    downloadSkillFile: downloadSkillFileMock,
    fetchImageObjectUrl: fetchImageObjectUrlMock,
  };
});

function makeMessage(over: Partial<Message> = {}): Message {
  return {
    id: 'm1',
    role: 'assistant',
    content: 'Bonjour',
    timestamp: new Date(),
    ...over,
  } as Message;
}

/**
 * B-1479 (recette P-146, lot 5, KO-6) : « aucune voie pour créer une
 * commande personnalisée ». La voie existe, sous chaque réponse, mais le
 * bouton s'appelait « Sauvegarder comme raccourci » (le menu « / », l'aide
 * et la modale parlent de commandes) et n'avait pas de nom accessible.
 */
describe('B-1479 : enregistrer une réponse comme commande', () => {
  it('le bouton porte le nom du geste : « Enregistrer comme commande »', () => {
    const onSave = vi.fn();
    render(<MessageBubble message={makeMessage({ role: 'assistant', content: 'Voici la relance.' })} onSaveAsCommand={onSave} />);
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme commande' }));
    expect(onSave).toHaveBeenCalledTimes(1);
  });
});

describe('B-1479 : la capacité « Skills et commandes » mène au vrai geste', () => {
  it('sa consigne ne demande pas au modèle de créer la commande, elle nomme le bouton', async () => {
    const { capabilities } = await import('../prototype/CapabilityCenter');
    const capacite = capabilities.find((c) => c.id === 'skills-commands');
    expect(capacite?.prompt).toContain('Enregistrer comme commande');
  });
});
