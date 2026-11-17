import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it, vi } from 'vitest';

// R4-3 : le bilan doit se tester même sans objets Git (archive ou clone nettoyé).
vi.mock('node:child_process', () => ({
  spawnSync: () => { throw new Error('R4-3 : aucun objet Git disponible pour le test documentaire'); },
}));

const bilan = () => readFileSync(resolve(__dirname, '../../../../docs/qualite/c20-front-maj.md'), 'utf8');

describe('Remédiation documentaire du lot front-maj', () => {
  it('R1-9 : B-1949 est qualifié comme amélioration, sans prétendre que le nom accessible manquait', () => {
    const ligne = bilan().split('\n').find((l) => l.startsWith('| B-1949 |'));
    expect(ligne).toContain('`amelioration`');
  });

  it('R1-10 : distingue la branche remise à la relecture des changements de cette passe', () => {
    const historique = bilan().split('## Remédiation de la relecture, passe 1')[0];
    expect(historique).toContain('f1087358');
    expect(historique).toContain('État remis à la relecture');
    expect(historique).toContain('c20/integration');
    for (const [id, rouge, correctif] of [
      ['B-1844', 'd805a3a4', '5ed7a868'],
      ['B-1845', '0198b00d', 'd5568587'],
      ['B-1949', '97e8ff6f', '61f1a8f9'],
      ['B-1950', '90e29bad', 'f1087358'],
    ]) {
      const ligne = historique.split('\n').find((l) => l.startsWith(`| ${id} |`));
      expect(ligne).toContain(rouge);
      expect(ligne).toContain(correctif);
    }
    expect(historique.split('\n').filter((l) => l.startsWith('| B-')).join('\n')).not.toContain('non commité');
  });

  it('R2-5 : conserve l’état historique de la passe 1 commitée', () => {
    const texte = bilan();
    const passe1 = texte.split('## Remédiation de la relecture, passe 1')[1]
      ?.split('## Remédiation de la relecture, passe 2')[0];
    const etatPasse1 = passe1?.split('### Décisions et correctifs')[0];
    expect(etatPasse1).toContain('6ab9f8cf');
    expect(etatPasse1).toContain('7c94e52a');
    expect(etatPasse1).toContain('commitée');
    expect(etatPasse1).not.toContain('restent non commités');
    expect(passe1).not.toContain('cette passe non commitée');
  });

  it('R3-5 : conserve le récit historique de la passe 2 commitée et de la reprise en passe 3', () => {
    const texte = bilan();
    const introduction = texte.split('## Verdicts et preuves')[0];
    const passe2 = texte.split('## Remédiation de la relecture, passe 2')[1]
      ?.split('## Remédiation de la relecture, passe 3')[0];
    const etatPasse2 = passe2?.split('### Constats et corrections')[0];
    expect(introduction).toContain('État reçu pour la passe 3 : HEAD `d3e815e7`');
    for (const commit of ['fefd0e1d', 'd3e815e7', '75498edd']) {
      expect(introduction).toContain(commit);
      expect(etatPasse2).toContain(commit);
    }
    expect(etatPasse2).toContain('commitée');
    expect(etatPasse2).toContain('Départ historique');
    expect(etatPasse2).toContain('7c94e52a');
    expect(etatPasse2).not.toContain('restent non commités');
    expect(introduction).toContain('« Remédiation de la relecture, passe 3 »');
    expect(introduction).toContain('`75498edd` est un ancêtre du lot reçu');
    expect(texte).toContain('## Remédiation de la relecture, passe 3');
  });

  it('R4-4 : distingue les passes commitées des changements actuels et clôt les retards intégrés', () => {
    const texte = bilan();
    const introduction = texte.split('## Verdicts et preuves')[0];
    expect(introduction).toContain('État reçu pour la passe 4');
    const etatActuel = introduction.split('Historique avant les rebases')[0];
    expect(etatActuel).toContain('passe 3 commitée');
    expect(etatActuel).toContain('`a498d9d3` et `31e3f98d` sont des ancêtres de HEAD');
    expect(etatActuel).toContain('retard d’instrumentation');
    expect(etatActuel).toContain('résolu');
    expect(etatActuel).toContain('c20/integration');
    expect(introduction).toContain('« Remédiation de la relecture, passe 4 » décrit le travail actuel');
    expect(introduction).not.toContain('cette nouvelle ascendance manque encore au lot');
    const passe3 = texte.split('## Remédiation de la relecture, passe 3')[1]
      ?.split('## Remédiation de la relecture, passe 4')[0];
    const etatPasse3 = passe3?.split('### Constats et corrections')[0];
    expect(etatPasse3).toContain('passe 3 commitée');
    expect(etatPasse3).not.toContain('restent non commités');
    expect(passe3).toContain('VERDICT HISTORIQUE : NO-GO');
  });

  it('R4-5 : la procédure Linux décrit aussi Ubuntu et ses dérivées sans le mot debian', () => {
    const procedure = readFileSync(resolve(__dirname, '../../../../docs/UPDATER-SETUP.md'), 'utf8');
    const controle = procedure.split('## Contrôle du manifeste Linux (B-1111)')[1]?.split('## Clés')[0];
    expect(controle).toMatch(/mot exact\s+`debian` ou `ubuntu`/);
    expect(controle).toContain('`ID` et `ID_LIKE`');
    expect(controle).toContain('`ID=ubuntu` sans `ID_LIKE`');
    expect(controle).toContain('`ID=pop` avec `ID_LIKE=ubuntu`');
  });
});
