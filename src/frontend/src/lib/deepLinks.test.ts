/**
 * B-072 - quatre-vingt-dix liens profonds sur quatre-vingt-seize étaient
 * ignorés en silence.
 *
 * `?panel=` a longtemps été LE mode d'ouverture d'une surface : chaque panneau
 * vivait dans sa propre fenêtre Tauri chargée sur `index.html?panel=xxx`
 * (DEVLOG:657, RULES-FRONTEND:269). Le retrait du mode classic (J0b) a fait des
 * panneaux des VUES adressables par `?view=`, et `PANNEAUX` s'est réduit à
 * `board` et `atelier` - sans que rien ne réponde aux anciennes valeurs.
 *
 * Le silence est le vrai défaut : `resolveDeepLinkPanel` rend `null`,
 * l'application ouvre son accueil, et le scénario qui attendait un écran
 * conclut sur un `wait_for` expiré plutôt que sur une erreur. Sur les 96
 * occurrences relevées dans `tests/protocols/`, 90 désignaient une valeur
 * ignorée (invoices 22, crm 21, tasks 19, calendar 14, memory 7, email 4,
 * chat 1, settings 1, data 1).
 *
 * Le correctif est un ALIAS de compatibilité, pas une nouvelle grammaire :
 * `?panel=<vue>` vaut `?view=<vue>`, `?panel=settings` vaut
 * `?action=settings.open`. Un paramètre explicite garde toujours la main.
 */
import { describe, expect, it } from 'vitest';

import { APP_VIEWS } from '../stores/navigationStore';
import {
  resolveDeepLinkAction,
  resolveDeepLinkPanel,
  resolveDeepLinkView,
} from './deepLinks';

describe('B-072 - un ?panel= hérité ouvre bien sa surface', () => {
  it.each(['crm', 'invoices', 'tasks', 'calendar', 'memory', 'email', 'chat'])(
    '?panel=%s ouvre la vue du même nom',
    (valeur) => {
      expect(resolveDeepLinkView(`?panel=${valeur}`)).toBe(valeur);
    },
  );

  it('?panel=settings ouvre les Réglages', () => {
    expect(resolveDeepLinkAction('?panel=settings')).toBe('settings.open');
  });

  it('aucune vue de l’application n’est laissée hors de l’alias', () => {
    // Le catalogue fait foi : une vue ajoutée demain reste adressable.
    for (const vue of APP_VIEWS) {
      expect(resolveDeepLinkView(`?panel=${vue}`)).toBe(vue);
    }
  });

  it('un ?view= explicite garde la main sur l’alias', () => {
    expect(resolveDeepLinkView('?view=email&panel=crm')).toBe('email');
    expect(resolveDeepLinkAction('?action=guided.open&panel=settings')).toBe('guided.open');
  });

  it('les deux vrais panneaux ne deviennent pas des vues', () => {
    // Sinon `?panel=board` déclencherait À LA FOIS l'ouverture d'une vue et
    // celle du Board.
    expect(resolveDeepLinkPanel('?panel=board')).toBe('board');
    expect(resolveDeepLinkPanel('?panel=atelier')).toBe('atelier');
    expect(resolveDeepLinkView('?panel=board')).toBeNull();
    expect(resolveDeepLinkView('?panel=atelier')).toBeNull();
  });

  it('une valeur qui ne désigne rien reste sans effet', () => {
    expect(resolveDeepLinkView('?panel=nimporte-quoi')).toBeNull();
    expect(resolveDeepLinkPanel('?panel=nimporte-quoi')).toBeNull();
    expect(resolveDeepLinkAction('?panel=nimporte-quoi')).toBeNull();
  });

  it('témoin : les résolutions nominales sont intactes', () => {
    expect(resolveDeepLinkView('?view=tasks')).toBe('tasks');
    expect(resolveDeepLinkView('?view=inconnue')).toBeNull();
    expect(resolveDeepLinkAction('?action=settings.open')).toBe('settings.open');
    expect(resolveDeepLinkAction('')).toBeNull();
  });
});
