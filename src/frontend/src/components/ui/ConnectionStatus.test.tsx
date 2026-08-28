/**
 * Campagne dix personas (28/08), finding F4 de la magistrate.
 *
 * Elle prépare ses interventions dans le train et cherche un état « hors
 * ligne ». L'en-tête affiche « Connecté », avec une icône Wifi. Or ce bandeau
 * ne parle pas du réseau : il reflète le health-check du MOTEUR LOCAL (le
 * sidecar backend). Sans réseau, l'application affiche donc « Connecté ».
 *
 * Son verdict : « "Souveraine" et "100 % local" ne veulent rien dire si une
 * recherche part dès que le réseau existe, et si rien ne me dit quand il
 * n'existe pas. »
 *
 * Ce lot ne branche PAS la détection réseau (`useOnlineStatus` existe et
 * n'est utilisé nulle part — c'est un autre chantier). Il fait seulement en
 * sorte que le bandeau cesse de PRÉTENDRE parler du réseau.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, beforeEach } from 'vitest';

import { useStatusStore } from '../../stores/statusStore';
import { ConnectionStatus } from './ConnectionStatus';

describe('Le bandeau d’état ne prétend plus parler du réseau', () => {
  beforeEach(() => {
    useStatusStore.setState({ connectionState: 'connected', latency: 12 } as never);
  });

  it('ne dit pas « Connecté » tout court : il nomme le moteur', () => {
    render(<ConnectionStatus />);

    // « Connecté », dans une application dite souveraine, se lit « connecté à
    // Internet ». Le mot doit désigner ce qu'il mesure.
    expect(screen.queryByText('Connecté')).toBeNull();
    expect(screen.getByText(/moteur/i)).toBeInTheDocument();
  });

  it('dit aussi le moteur quand il est arrêté', () => {
    useStatusStore.setState({ connectionState: 'disconnected', latency: null } as never);
    render(<ConnectionStatus />);

    expect(screen.queryByText('Déconnecté')).toBeNull();
    expect(screen.getByText(/moteur/i)).toBeInTheDocument();
  });
});
