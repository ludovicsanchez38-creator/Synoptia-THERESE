/**
 * B-1369 (persona Hugo, cycle 13) : pendant une réponse, un changement de vue
 * est refusé par un bandeau « Arrête la réponse avant de changer de vue ».
 * Ce bandeau, en bas à droite, recouvrait le bouton « Arrêter la réponse » du
 * composeur : le message demandait un geste et cachait le bouton pour le
 * faire. Le bandeau porte désormais lui-même l'arrêt, inscrit par le
 * composeur qui tient le flux.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../stores/chatStore';
import { useStatusStore } from '../stores/statusStore';
import { arreterLaReponse, inscrireArretDeLaReponse } from './arretDeLaReponse';
import { runNavigationAction } from './clientActions';

let desinscrire: (() => void) | null = null;

function dernierRefus() {
  return useStatusStore.getState().notifications.filter((n) => n.title === 'Réponse en cours').at(-1);
}

describe("B-1369 : le bandeau qui demande d'arrêter la réponse porte l'arrêt", () => {
  beforeEach(() => {
    useChatStore.setState({ isStreaming: true });
    useStatusStore.setState({ notifications: [] });
  });
  afterEach(() => {
    desinscrire?.();
    desinscrire = null;
    useChatStore.setState({ isStreaming: false });
  });

  it("le refus de navigation propose « Arrêter la réponse », qui arrête vraiment", () => {
    const arret = vi.fn();
    desinscrire = inscrireArretDeLaReponse(arret);

    expect(runNavigationAction('crm')).toBe(false);

    const refus = dernierRefus();
    expect(refus?.action?.label).toBe('Arrêter la réponse');
    refus?.action?.onClick();
    expect(arret).toHaveBeenCalledTimes(1);
  });

  it("sans composeur qui tient le flux, le bandeau ne promet pas de bouton", () => {
    runNavigationAction('crm');
    expect(dernierRefus()).toBeDefined();
    expect(dernierRefus()?.action).toBeUndefined();
  });

  it("un composeur démonté retire son arrêt, sans retirer celui d'un autre", () => {
    const ancien = vi.fn();
    const nouveau = vi.fn();
    const retirerAncien = inscrireArretDeLaReponse(ancien);
    desinscrire = inscrireArretDeLaReponse(nouveau);
    retirerAncien();

    expect(arreterLaReponse()).toBe(true);
    expect(nouveau).toHaveBeenCalledTimes(1);
    expect(ancien).not.toHaveBeenCalled();
  });
});
