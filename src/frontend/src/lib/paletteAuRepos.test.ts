/**
 * Entrée 1 du plan du 28/08 : la palette montre ce qu'elle sait faire.
 *
 * `visibleActions` rend une liste vide tant qu'on n'a rien tapé, alors que
 * « Ouvrir les Projets », « Ouvrir les Fichiers », « Nouveau document » et
 * « Exporter les données » sont câblées et attendent. Il faut deviner le mot
 * exact pour découvrir ce qui existe.
 *
 * La relecture a posé la condition : ne pas tout déverser. Les parcours de
 * l'établi et les capacités fréquentes sont déjà listés au-dessus ; répéter
 * leurs destinations ferait douter qu'il s'agisse des mêmes.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { actionsAuRepos } from './paletteAuRepos';

const ACTIONS = [
  { id: 'email.open', label: 'Ouvrir la messagerie' },
  { id: 'memory.open', label: 'Ouvrir les Contacts' },
  { id: 'invoices.open', label: 'Ouvrir la facturation' },
  { id: 'home.open', label: 'Ouvrir l’accueil' },
  { id: 'projects.open', label: 'Ouvrir les Projets' },
  { id: 'files.open', label: 'Ouvrir les Fichiers' },
  { id: 'documents.new', label: 'Nouveau document' },
  { id: 'data.export', label: 'Exporter les données' },
  { id: 'board.open', label: 'Ouvrir le Board' },
];

const PARCOURS = ['email', 'memory', 'meeting', 'invoice', 'board'];

describe('Ce que la palette propose avant qu’on tape', () => {
  it('propose les destinations que rien d’autre n’annonce', () => {
    const ids = actionsAuRepos(ACTIONS, PARCOURS, []).map((a) => a.id);

    expect(ids).toContain('projects.open');
    expect(ids).toContain('files.open');
    expect(ids).toContain('documents.new');
    expect(ids).toContain('data.export');
  });

  it('ne répète pas les parcours de l’établi', () => {
    const ids = actionsAuRepos(ACTIONS, PARCOURS, []).map((a) => a.id);

    expect(ids).not.toContain('email.open');
    expect(ids).not.toContain('memory.open');
    expect(ids).not.toContain('invoices.open');
  });

  it('ne répète pas une capacité déjà listée', () => {
    const ids = actionsAuRepos(ACTIONS, PARCOURS, ['files']).map((a) => a.id);

    expect(ids).not.toContain('files.open');
    expect(ids).toContain('projects.open');
  });

  it('n’annonce pas l’accueil, puisqu’on y est', () => {
    const ids = actionsAuRepos(ACTIONS, PARCOURS, []).map((a) => a.id);

    expect(ids).not.toContain('home.open');
  });

  it('reste une courte liste, pas un catalogue', () => {
    const beaucoup = Array.from({ length: 30 }, (_, i) => ({
      id: `truc${i}.open`,
      label: `Truc ${i}`,
    }));

    expect(actionsAuRepos(beaucoup, PARCOURS, []).length).toBeLessThanOrEqual(6);
  });

  it('est réellement branchée dans la coque', () => {
    const source = readFileSync(
      path.join(__dirname, '..', 'components', 'prototype', 'ConversationCanvasPrototype.tsx'),
      'utf8',
    );
    expect(source).toContain('actionsAuRepos(');
  });
});
