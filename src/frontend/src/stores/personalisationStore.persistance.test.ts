/**
 * B-493 (cycle 4) : le magasin de personnalisation persistait tout son état
 * sans partialize ni version : les gabarits de prompts revenaient du stockage
 * avec un createdAt en chaîne, et une table de raccourcis enregistrée une fois
 * restait figée. B-337 : cette table est retirée.
 */
import { beforeEach, describe, expect, it } from 'vitest';

import { usePersonalisationStore } from './personalisationStore';

describe('personalisationStore : persistance', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('ne persiste que les données, jamais les fonctions ni les raccourcis', () => {
    const options = usePersonalisationStore.persist.getOptions();
    const partiel = options.partialize!(usePersonalisationStore.getState()) as unknown as Record<string, unknown>;
    expect(Object.keys(partiel).sort()).toEqual(['llmBehavior', 'promptTemplates', 'skipDashboard', 'uxMode']);
    expect(Object.values(partiel).some((v) => typeof v === 'function')).toBe(false);
    expect(options.version).toBe(1);
  });

  it('la migration rend son type Date à createdAt et oublie les raccourcis enregistrés', () => {
    // Le stockage réel est cloisonné par profil et absent en test : la migration
    // s'exerce directement, comme le middleware l'appelle sur une version ancienne.
    const migrate = usePersonalisationStore.persist.getOptions().migrate!;
    const migre = migrate(
      {
        promptTemplates: [{ id: 't1', name: 'Relance', prompt: 'Bonjour', category: 'suivi', createdAt: '2026-09-01T10:00:00.000Z' }],
        shortcuts: [{ action: 'x', key: 'k', modifiers: [] }],
        uxMode: 'simple',
      },
      0,
    ) as { promptTemplates: { createdAt: Date }[]; shortcuts?: unknown; uxMode?: string };
    expect(migre.promptTemplates[0].createdAt).toBeInstanceOf(Date);
    expect(migre.promptTemplates[0].createdAt.getFullYear()).toBe(2026);
    expect('shortcuts' in migre).toBe(false);
    expect(migre.uxMode).toBe('simple');
  });
});
