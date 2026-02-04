/**
 * THÉRÈSE v2 - Panel Window
 *
 * Wrapper standalone pour les panels ouverts dans une fenêtre séparée.
 * Initialise l'auth API AVANT de rendre le panel, puis pré-charge
 * les comptes email si nécessaire (Email/Calendrier).
 */

import { useEffect, useState } from 'react';
import { initializeAuth, getEmailAuthStatus } from '../../services/api';
import { useEmailStore } from '../../stores/emailStore';
import { EmailPanel } from '../email';
import { CalendarPanel } from '../calendar';
import { TasksPanel } from '../tasks';
import { InvoicesPanel } from '../invoices';
import { CRMPanel } from '../crm';
import type { PanelType } from '../../services/windowManager';

interface PanelWindowProps {
  panel: PanelType;
}

export function PanelWindow({ panel }: PanelWindowProps) {
  const { setAccounts, setCurrentAccount, currentAccountId } = useEmailStore();

  // Toujours attendre l'init auth avant de rendre le panel
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        // 1. Initialiser le token d'auth (obligatoire avant tout appel API)
        await initializeAuth();

        // 2. Pour email et calendrier, pré-charger les comptes
        if (panel === 'email' || panel === 'calendar') {
          try {
            const status = await getEmailAuthStatus();
            if (status.accounts.length > 0) {
              setAccounts(status.accounts);
              if (!currentAccountId) {
                setCurrentAccount(status.accounts[0].id);
              }
            }
          } catch (e) {
            console.warn('Could not refresh email accounts:', e);
          }
        }

        setReady(true);
      } catch (e) {
        console.error('PanelWindow init failed:', e);
        setError('Erreur de connexion au backend');
      }
    }
    init();
  }, []);

  if (error) {
    return (
      <div className="h-screen w-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent">
            THÉRÈSE
          </h1>
          <p className="text-red-400 mt-2 text-sm">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 rounded-lg bg-accent-cyan/20 text-accent-cyan text-sm hover:bg-accent-cyan/30 transition-colors"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  if (!ready) {
    return (
      <div className="h-screen w-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent">
            THÉRÈSE
          </h1>
          <p className="text-text-muted mt-2 text-sm">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-bg text-text overflow-hidden">
      {panel === 'email' && <EmailPanel standalone />}
      {panel === 'calendar' && <CalendarPanel standalone />}
      {panel === 'tasks' && <TasksPanel standalone />}
      {panel === 'invoices' && <InvoicesPanel standalone />}
      {panel === 'crm' && <CRMPanel standalone />}
    </div>
  );
}
