/**
 * DA « Application affinée », lot 6 : les SIX fichiers de l'écran Projets et
 * tâches, en un seul endroit.
 *
 * Deux gardes de source les parcourent — les couleurs en dur
 * (`components/ui/aucuneCouleurEnDur.test.ts`) et le plancher de taille des
 * boutons (`lot6DA.test.ts`). Une liste recopiée par garde, c'est une garde
 * qui oublie un fichier le jour où le lot en gagne un.
 *
 * Module de test (lu par `node:path`), jamais importé par l'application.
 */
import path from 'node:path';

/** Chemins relatifs à `src/`. */
export const FICHIERS_LOT6 = [
  'components/tasks/TasksPanel.tsx',
  'components/tasks/TaskKanban.tsx',
  'components/tasks/TaskList.tsx',
  'components/tasks/TaskForm.tsx',
  'components/memory/ProjectsPanel.tsx',
  'components/memory/ProjectsKanban.tsx',
] as const;

const SRC = path.resolve(__dirname, '..');

/** Les mêmes, en absolu. */
export const CHEMINS_LOT6: string[] = FICHIERS_LOT6.map((f) => path.join(SRC, f));
