import { expect, it } from 'vitest';
import * as ts from 'typescript';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { installReadOnlyShell, type RouteLectureSeule } from '../../../../tests/e2e/stories/helpers/garde-lecture-seule';

async function installerGarde() {
  let garde!: (route: RouteLectureSeule) => Promise<void>;
  await installReadOnlyShell({
    route: async (motif, gestionnaire) => {
      expect(motif).toBe('http://127.0.0.1:31999/**');
      garde = gestionnaire;
    },
  }, 'http://127.0.0.1:31999');

  return async function simuler(methode: string, chemin: string) {
    let resultat: unknown;
    await garde({
      request: () => ({ url: () => `http://127.0.0.1:31999${chemin}`, method: () => methode }),
      continue: async () => { resultat = 'moteur'; },
      fulfill: async (reponse) => { resultat = reponse; },
    });
    return resultat;
  };
}

it('refuse les mutations sur les routes bouchonnées', async () => {
  const simuler = await installerGarde();
  for (const chemin of ['/api/images/generate', '/api/tasks', '/api/config/profile']) {
    expect(await simuler('POST', chemin)).toMatchObject({ status: 405 });
  }
  expect(await simuler('GET', '/api/tasks')).toMatchObject({ status: 200 });
});

it('laisse le calcul pur rejoindre le moteur', async () => {
  const simuler = await installerGarde();
  expect(await simuler('POST', '/api/calc/roi')).toBe('moteur');
});

it('refuse une mutation non prévue sans charger Playwright', async () => {
  const simuler = await installerGarde();
  expect(await simuler('POST', '/api/inconnue')).toMatchObject({ status: 405 });
});

it('installe la garde dans le beforeEach du parcours', () => {
  const sourceParcours = readFileSync(resolve(__dirname, '../../../../tests/e2e/stories/parcours-08-capacites-prototype.spec.ts'), 'utf8');
  const source = ts.createSourceFile('parcours.ts', sourceParcours, ts.ScriptTarget.Latest, true);
  let gardeInstallee = false;
  function examiner(noeud: ts.Node) {
    if (ts.isCallExpression(noeud) && noeud.expression.getText(source) === 'test.beforeEach') {
      const initialisation = noeud.arguments[0];
      if (initialisation && ts.isArrowFunction(initialisation) && ts.isBlock(initialisation.body)) {
        gardeInstallee ||= initialisation.body.statements.some((instruction) => {
          if (!ts.isExpressionStatement(instruction) || !ts.isAwaitExpression(instruction.expression)) return false;
          const appel = instruction.expression.expression;
          return ts.isCallExpression(appel) && appel.expression.getText(source) === 'installReadOnlyShell'
            && appel.arguments.map((argument) => argument.getText(source)).join(',') === 'page,BACKEND_URL';
        });
      }
    }
    ts.forEachChild(noeud, examiner);
  }
  examiner(source);
  expect(gardeInstallee).toBe(true);
});
