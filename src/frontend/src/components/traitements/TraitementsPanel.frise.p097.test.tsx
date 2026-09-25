/**
 * P-097 (acceptée par Ludo le 24/09/2026, suggestion S2 de Dr_logic-3D),
 * version minimale : les travaux récents se lisent comme une frise en lecture
 * seule. Les étapes passées n'ont plus l'apparence d'un bouton (carte bordée),
 * et chaque travail dit son état, son heure de début et, s'il est fini, son
 * heure de fin. Vérifié d'abord sur une vraie indexation (122 s, pile jetable
 * du cycle 12) : le registre garde created_at, started_at et finished_at, en
 * UTC SANS fuseau ; les lire comme heure locale décalerait de deux heures.
 */
import { render, screen, within } from '@testing-library/react';
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({ listerTraitements: vi.fn(), annulerTraitement: vi.fn() }));

import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { TraitementsPanel } from './TraitementsPanel';

const TZ = process.env.TZ;
beforeAll(() => { process.env.TZ = 'Europe/Paris'; });
afterAll(() => { process.env.TZ = TZ; });

const base = {
  type: 'indexation', step: null, progress: null, project_id: null, conversation_id: null,
  error: null, created_at: '2026-09-24T08:57:46.552141', can_cancel: false,
};

describe('P-097 : frise des travaux récents', () => {
  beforeEach(() => {
    useProcessingTasksStore.setState({
      erreur: null, arretsDemandes: new Set(), panneauOuvert: true,
      traitements: [
        { ...base, id: 't2', label: 'rapport-long-c12.txt', state: 'running', started_at: '2026-09-24T09:10:00', finished_at: null, can_cancel: true },
        { ...base, id: 't1', label: 'note.txt', state: 'done', started_at: '2026-09-24T08:57:46.555773', finished_at: '2026-09-24T08:59:48.291268' },
      ],
    } as never);
  });

  it('une liste ordonnée, sans étape présentée comme un bouton', () => {
    render(<TraitementsPanel />);
    const frise = screen.getByRole('list', { name: 'Frise des travaux récents' });
    // Audit de release 0.75 : WebKit (Safari, Tauri sous macOS) retire la
    // sémantique de liste d'un <ol> sans puces ; VoiceOver ne l'annonce plus.
    // Le rôle explicite la rétablit (jsdom ne reproduit pas ce retrait).
    expect(frise).toHaveAttribute('role', 'list');
    expect(frise.tagName).toBe('OL');
    const passe = within(frise).getAllByRole('listitem')[1];
    // Ni bordure ni fond de carte (la pastille de la frise est un pseudo-élément).
    const classes = passe.className.split(/\s+/);
    expect(classes.filter((c) => c === 'border' || c.startsWith('border-') || c === 'bg-surface-2')).toEqual([]);
    // P-140 (acceptée après P-097) : une étape passée peut ouvrir l'objet
    // qu'elle nomme. Ce geste est un lien de texte, jamais une carte-bouton.
    for (const geste of within(passe).queryAllByRole('button')) {
      expect(geste).toHaveAccessibleName(/^Ouvrir /);
      expect(geste.className.split(/\s+/).filter((c) => c === 'border' || c.startsWith('border-') || c.startsWith('bg-'))).toEqual([]);
    }
  });

  it('un travail fini dit son état, son début et sa fin, en heure locale (UTC du serveur)', () => {
    render(<TraitementsPanel />);
    const passe = within(screen.getByRole('list', { name: 'Frise des travaux récents' })).getAllByRole('listitem')[1];
    expect(passe).toHaveTextContent('Terminé');
    expect(passe).toHaveTextContent('Début 10:57');
    expect(passe).toHaveTextContent('Fin 10:59');
  });

  it('un travail en cours dit son début, sans fin, et garde « Arrêter »', () => {
    render(<TraitementsPanel />);
    const enCours = within(screen.getByRole('list', { name: 'Frise des travaux récents' })).getAllByRole('listitem')[0];
    expect(enCours).toHaveTextContent('Début 11:10');
    expect(enCours).not.toHaveTextContent('Fin');
    expect(within(enCours).getByRole('button', { name: /Arrêter/ })).toBeInTheDocument();
  });
});
