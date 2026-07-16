import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

function source(relativePath: string): string {
  return readFileSync(join(process.cwd(), 'src/components', relativePath), 'utf8');
}

describe('contrat responsive de la coque 0.40', () => {
  it('empile les parcours denses avant leurs breakpoints', () => {
    expect(source('onboarding/WelcomeStep.tsx')).toMatch(/grid-cols-1[^"\n]*sm:grid-cols-3/);
    expect(source('settings/SettingsModal.tsx')).toContain('flex-col overflow-hidden sm:flex-row');
    expect(source('settings/SettingsModal.tsx')).toContain('overflow-x-auto');
    expect(source('prototype/ContactsMemoryCard.tsx')).toContain('grid-rows-[minmax(160px,40%)_minmax(0,1fr)]');
    expect(source('prototype/ContactsMemoryCard.tsx')).toContain('sm:grid-cols-[210px_minmax(0,1fr)]');
    const capabilityCenter = source('prototype/CapabilityCenter.tsx');
    expect(capabilityCenter).toContain('flex-col md:flex-row');
    expect(capabilityCenter).toContain('left-4 right-4');
    expect(capabilityCenter).toContain('sm:left-auto sm:w-[360px]');
  });

  it('n’affiche plus les trois fausses commandes macOS dans la coque principale', () => {
    const shell = source('prototype/ConversationCanvasPrototype.tsx');
    expect(shell).not.toContain('bg-[#FF5F57]');
    expect(shell).not.toContain('bg-[#FFBD2E]');
    expect(shell).not.toContain('bg-[#28C840]');
  });
});
