/**
 * Comptes email — le chemin depuis les Réglages (0.44).
 *
 * L'inventaire du 13/08 a établi que l'assistant de configuration email n'a
 * AUCUN chemin par les Réglages : la rubrique Services ne contenait que
 * Images, Transcription vocale, Recherche Web et Extraction automatique. Le
 * testeur l'a redit le 18/08 : « les paramètres de la messagerie devraient,
 * comme tout le reste, se trouver dans paramètres ».
 *
 * Cette section ne déplace PAS l'assistant : il vit dans la vue Email et y
 * reste — le dupliquer ici créerait une huitième déclaration concurrente,
 * l'inverse du chantier en cours. Elle donne le CHEMIN : voir ses comptes,
 * et y aller en un clic.
 */
import { useEffect, useState } from 'react';
import { Mail } from 'lucide-react';

import { getEmailAuthStatus } from '../../services/api/email';
import { usePanelStore } from '../../stores/panelStore';
import { useNavigationStore } from '../../stores/navigationStore';

interface CompteAffiche {
  id: string;
  email: string;
  provider: string;
}

export function EmailAccountsSection() {
  const [comptes, setComptes] = useState<CompteAffiche[] | null>(null);
  const [illisible, setIllisible] = useState(false);

  useEffect(() => {
    let vivant = true;
    getEmailAuthStatus()
      .then((statut) => {
        if (vivant) setComptes(statut.accounts ?? []);
      })
      .catch(() => {
        // Le bouton EST la fonctionnalité : un backend grognon ne doit pas
        // le faire disparaître — ce serait recréer l'impasse qu'on corrige.
        if (vivant) {
          setComptes([]);
          setIllisible(true);
        }
      });
    return () => {
      vivant = false;
    };
  }, []);

  const ouvrirConfiguration = () => {
    usePanelStore.getState().closeSettings();
    useNavigationStore.getState().setView('email');
  };

  return (
    <div className="p-4 bg-background/40 border border-border/40 rounded-md">
      <div className="flex items-center gap-2 mb-2">
        <Mail className="w-4 h-4 text-accent-cyan-ink" />
        <h3 className="font-medium text-text">Comptes email</h3>
      </div>

      {comptes === null ? (
        <p className="text-sm text-text-muted">Chargement…</p>
      ) : comptes.length > 0 ? (
        <ul className="mb-3 space-y-1">
          {comptes.map((compte) => (
            <li key={compte.id} className="text-sm text-text">
              {compte.email}
              <span className="ml-2 text-xs text-text-muted">
                {compte.provider}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mb-3 text-sm text-text-muted">
          {illisible
            ? 'Impossible de lire les comptes pour le moment.'
            : 'Aucun compte connecté.'}
        </p>
      )}

      <button
        type="button"
        data-testid="email-accounts-open"
        onClick={ouvrirConfiguration}
        className="text-sm font-semibold text-text underline underline-offset-2"
      >
        Ouvrir la configuration email
      </button>
      <p className="mt-1 text-xs text-text-muted">
        Connexion, ajout de comptes et signature se règlent dans la vue Email.
      </p>
    </div>
  );
}
