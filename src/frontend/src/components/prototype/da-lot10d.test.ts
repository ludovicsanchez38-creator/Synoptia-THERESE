import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const FILES = [
  'components/prototype/FollowUpsWorkspaceCanvas.tsx',
  'components/prototype/VoiceWorkspaceCanvas.tsx',
  'components/prototype/ImagesWorkspaceCanvas.tsx',
  'components/prototype/CalculatorWorkspaceCanvas.tsx',
  'components/prototype/DeliverablesWorkspaceCanvas.tsx',
  'components/chat/CommandPalette.tsx',
  'components/chat/ShortcutsModal.tsx',
  'components/traitements/TraitementsPanel.tsx',
  'components/ui/NotificationCenter.tsx',
  'components/prompts/PromptLibrary.tsx',
  'components/prototype/CapabilityCenter.tsx',
  'components/settings/AboutTab.tsx',
] as const;

const sources = FILES.map((file) => ({
  file,
  source: readFileSync(resolve(process.cwd(), 'src', file), 'utf8'),
}));

describe('lot 10D DA : espaces de travail et panneaux transverses', () => {
  it('n’introduit ni ombre RGBA locale ni dégradé', () => {
    const findings = sources.flatMap(({ file, source }) => {
      const matches = source.match(/shadow-\[[^\n]+|\bbg-gradient-\S+/g) ?? [];
      return matches.map((match) => `${file}: ${match}`);
    });

    expect(findings).toEqual([]);
  });

  it('ne grossit aucun bouton au survol ou à l’activation', () => {
    const findings = sources.flatMap(({ file, source }) => {
      const matches = source.match(/(?:hover|active):scale-[^\s"'`]+/g) ?? [];
      return matches.map((match) => `${file}: ${match}`);
    });

    expect(findings).toEqual([]);
  });

  it('fait reposer les cinq canevas sur les primitives partagées', () => {
    for (const { file, source } of sources.slice(0, 5)) {
      expect(source, file).toMatch(/import \{[^}]*Button[^}]*\} from '\.\.\/ui';/s);
    }
  });
});
