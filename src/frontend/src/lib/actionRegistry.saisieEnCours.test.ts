/**
 * Revue Codex n°14 du cycle 11 (23/09/2026), R-3 et R-4 (B-1003).
 *
 * Une action de navigation du registre (raccourci, accueil, palette, pont
 * de recette) s'exécutait avant que la coque ne consulte la saisie en
 * cours : « Accueil » vidait l'historique et « Nouveau document » posait sa
 * demande de modale, même quand un formulaire modifié retenait la sortie.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { runAction } from './actionRegistry';
import { _viderSaisiesEnCours, inscrireSaisieEnCours } from './saisieEnCours';
import { useDocumentStore } from '../stores/documentStore';
import { useNavigationStore } from '../stores/navigationStore';

beforeEach(() => {
  _viderSaisiesEnCours();
  useNavigationStore.setState({ activeView: 'tasks', history: ['memory'] } as never);
  useDocumentStore.setState({ createModalRequested: false } as never);
});
afterEach(() => _viderSaisiesEnCours());

describe('B-1003 : le registre consulte la saisie en cours avant une navigation', () => {
  it('« Accueil » retenu : ni la vue ni l’historique ne changent', () => {
    const garde = vi.fn(() => true);
    inscrireSaisieEnCours(garde);
    runAction('home.open');
    expect(garde).toHaveBeenCalledTimes(1);
    expect(useNavigationStore.getState().activeView).toBe('tasks');
    expect(useNavigationStore.getState().history).toEqual(['memory']);
  });

  it('« Nouveau document » retenu : aucune demande de modale ne reste en attente', () => {
    inscrireSaisieEnCours(() => true);
    runAction('documents.new');
    expect(useNavigationStore.getState().activeView).toBe('tasks');
    expect(useDocumentStore.getState().createModalRequested).toBe(false);
  });

  it('vue déjà affichée : aucune question, l’action s’exécute', () => {
    const garde = vi.fn(() => true);
    inscrireSaisieEnCours(garde);
    runAction('tasks.open');
    expect(garde).not.toHaveBeenCalled();
  });

  it('témoin : sans saisie retenue, « Accueil » ramène à l’accueil', () => {
    runAction('home.open');
    expect(useNavigationStore.getState().activeView).toBeNull();
  });
});
