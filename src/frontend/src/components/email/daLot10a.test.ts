/**
 * DA « Application affinée », lot 10A : messagerie et mise en route.
 *
 * Ces gardes portent sur les régressions qui avaient dispersé ces écrans :
 * effets de grossissement, dégradés locaux, couleurs littérales et texte à
 * 12 px dans un contrôle. Les tests fonctionnels voisins restent la preuve
 * des appels, validations et consentements inchangés.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINES = [__dirname, join(__dirname, '..', 'onboarding')];

function sourcesDeProduction() {
  return RACINES.flatMap((racine) =>
    (readdirSync(racine, { recursive: true }) as string[])
      .filter((nom) => /\.(?:ts|tsx)$/.test(nom) && !/\.test\.(?:ts|tsx)$/.test(nom))
      .map((nom) => ({ nom: join(racine, nom), source: readFileSync(join(racine, nom), 'utf8') })),
  );
}

describe('Lot 10A DA : contrat transversal', () => {
  it('n’introduit ni dégradé, ni grossissement interactif, ni couleur littérale', () => {
    for (const fichier of sourcesDeProduction()) {
      expect(fichier.source, fichier.nom).not.toMatch(/\bbg-gradient\b|\bwhile(?:Hover|Tap)\b/);
      expect(fichier.source, fichier.nom).not.toMatch(/(?:['"]|\[)#[0-9a-f]{3,8}\b|rgba?\s*\(/i);
    }
  });

  it('garde 14 px minimum dans les contrôles HTML composés localement', () => {
    for (const fichier of sourcesDeProduction()) {
      const interactifs = [
        ...(fichier.source.match(/<(?:motion\.)?button\b[\s\S]*?<\/(?:motion\.)?button>/g) ?? []),
        ...(fichier.source.match(/<summary\b[\s\S]*?<\/summary>/g) ?? []),
        ...(fichier.source.match(/<label\b[\s\S]*?<\/label>/g) ?? []).filter((bloc) => /<(?:input|select|textarea)\b/.test(bloc)),
      ];
      expect(interactifs.filter((bloc) => /\btext-xs\b/.test(bloc)), fichier.nom).toEqual([]);
    }
  });

  it('ancre les formulaires et états majeurs sur les primitives partagées', () => {
    const exigences = [
      ['EmailCompose.tsx', ['FormField', 'Input', 'Textarea', 'Alerte']],
      ['ResponseGeneratorModal.tsx', ['Carte', 'Segments', 'Textarea', 'Button']],
      ['SignatureEditorModal.tsx', ['Carte', 'FormField', 'Textarea', 'Button']],
      [join('wizard', 'SmtpConfigStep.tsx'), ['FormField', 'Input', 'Select', 'Alerte']],
      [join('..', 'onboarding', 'ProfileStep.tsx'), ['FormField', 'Input', 'Textarea', 'Alerte']],
    ] as const;

    for (const [relatif, primitives] of exigences) {
      const source = readFileSync(join(__dirname, relatif), 'utf8');
      for (const primitive of primitives) expect(source, relatif).toContain(`<${primitive}`);
    }
  });

  it('fait passer les actions sous le titre avant 840 px', () => {
    for (const nom of ['EmailPanel.tsx', 'EmailCompose.tsx']) {
      expect(readFileSync(join(__dirname, nom), 'utf8'), nom).toContain('max-[840px]:basis-full');
    }
  });
});
