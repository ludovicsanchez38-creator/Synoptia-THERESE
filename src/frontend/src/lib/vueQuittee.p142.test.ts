/**
 * P-142 (persona Zoé, cycle 13) : après un rechargement, l'application
 * revenait toujours à l'Accueil. L'écran quitté est gardé pour la session
 * (sessionStorage : il survit au rechargement, pas à la fermeture).
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { lienProfondPresent, lireLaVueQuittee, memoriserLaVue } from './vueQuittee';

describe('P-142 : l’écran quitté', () => {
  beforeEach(() => sessionStorage.clear());

  it('une vue mémorisée se relit, l’accueil l’efface', () => {
    memoriserLaVue('documents');
    expect(lireLaVueQuittee()).toBe('documents');
    memoriserLaVue(null);
    expect(lireLaVueQuittee()).toBeNull();
  });

  it('une valeur inconnue ou le chat ne se rouvrent pas', () => {
    sessionStorage.setItem('therese:vue-quittee', 'nimporte-quoi');
    expect(lireLaVueQuittee()).toBeNull();
    memoriserLaVue('chat');
    expect(lireLaVueQuittee()).toBeNull();
  });

  it('un lien profond l’emporte sur l’écran quitté', () => {
    expect(lienProfondPresent('?view=crm')).toBe(true);
    expect(lienProfondPresent('?interface=conversation-canvas&scenario=email')).toBe(true);
    expect(lienProfondPresent('?interface=conversation-canvas')).toBe(false);
  });
});
