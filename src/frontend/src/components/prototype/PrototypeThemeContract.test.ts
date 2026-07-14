import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const directory = join(process.cwd(), 'src/components/prototype');
const componentSources = readdirSync(directory)
  .filter((name) => name.endsWith('.tsx') && !name.endsWith('.test.tsx'))
  .map((name) => ({ name, source: readFileSync(`${directory}/${name}`, 'utf8') }));

describe('contrat de thème de la coque 0.40', () => {
  it('utilise les tokens clair/sombre pour les surfaces et textes neutres', () => {
    const forbiddenNeutralClasses = [
      'bg-[#F3F6FC]',
      'bg-[#F7F9FD]',
      'bg-[#F8FAFD]',
      'bg-white',
      'text-[#101C36]',
      'text-[#33415C]',
      'text-[#5B6A82]',
      'text-[#7B8AA3]',
      'border-[#DCE4F1]',
      'border-[#E4EAF3]',
    ];

    for (const { name, source } of componentSources) {
      for (const className of forbiddenNeutralClasses) {
        expect(source, `${name} ne doit pas figer ${className}`).not.toContain(className);
      }
    }
  });

  it('conserve les portraits générés pour les identités principales', () => {
    const combined = componentSources.map(({ source }) => source).join('\n');
    expect(combined).toContain("url('/prototype/therese-character-atlas-v1.png')");
    expect(combined.match(/<CharacterPortrait/g)?.length ?? 0).toBeGreaterThanOrEqual(12);
  });
});
