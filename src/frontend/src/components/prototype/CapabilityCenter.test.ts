import { describe, expect, it } from 'vitest';
import { capabilities, capabilityGroups } from './CapabilityCenter';

describe('catalogue des capacités 0.40', () => {
  it('conserve les 30 capacités validées dans le prototype', () => {
    expect(capabilities).toHaveLength(30);
  });

  it('utilise un identifiant unique pour chaque capacité', () => {
    const ids = capabilities.map((capability) => capability.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('préserve explicitement chaque capacité du périmètre 0.40', () => {
    expect(capabilities.map((capability) => capability.id).sort()).toEqual([
      'actions',
      'agents',
      'attention',
      'billing',
      'calculators',
      'calendar',
      'contacts-memory',
      'crm',
      'daily-brief',
      'decision-board',
      'deliverables',
      'document-workshop',
      'email',
      'files-rag',
      'images',
      'legal',
      'mcp',
      'office',
      'personalization',
      'privacy',
      'profile',
      'projects',
      'prompts-variables',
      'providers',
      'security',
      'skills-commands',
      'tasks',
      'usage',
      'voice',
      'web-research',
    ]);
  });

  it('rattache chaque capacité à une intention connue', () => {
    const groupIds = new Set(capabilityGroups.map((group) => group.id));
    expect(capabilityGroups).toHaveLength(6);

    for (const capability of capabilities) {
      expect(groupIds.has(capability.group)).toBe(true);
    }
  });

  it('préserve la répartition fonctionnelle du prototype', () => {
    const counts = Object.fromEntries(
      capabilityGroups.map((group) => [
        group.id,
        capabilities.filter((capability) => capability.group === group.id).length,
      ]),
    );

    expect(counts).toEqual({
      organize: 5,
      business: 5,
      create: 5,
      decide: 5,
      automate: 4,
      control: 6,
    });
  });
});
