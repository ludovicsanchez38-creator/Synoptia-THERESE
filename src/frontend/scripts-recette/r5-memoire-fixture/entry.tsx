import React from 'react';
import { createRoot } from 'react-dom/client';
import { AgentMemoryPanel } from '../../src/frontend/src/components/memory/AgentMemoryPanel';
import { useDemoStore } from '../../src/frontend/src/stores/demoStore';
import './style.css';
const card = { id: 'fiche', kind: 'decision', title: 'Acompte décidé', content: 'Demande un acompte de 30 % avant la séance.',
  reason: 'Réserve le créneau.', version: 1, protected: true, author: 'therese', last_author: 'utilisateur',
  scope: 'global', scope_name: 'Général', state: 'active', created_at: '2026-10-21T10:00:00Z', updated_at: '2026-10-21T10:00:00Z' };
const trace = { id: 'trace', type: 'agent_action', title: 'Envoi de mail', contact_id: null,
  description: null, extra_data: '{"outcome":"indeterminee"}', statut: 'en_vigueur', created_at: '2026-10-21T10:00:00Z' };
window.fetch = async input => {
  const url = new URL(String(input), location.href); let data: unknown;
  if (url.pathname.endsWith('/cards/scopes')) data = [];
  else if (url.pathname === '/api/memory/cards') data = { items: [card], total: 1 };
  else if (url.pathname === '/api/memory/cards/fiche') data = card;
  else if (url.pathname === '/api/crm/activities') data = url.searchParams.get('type') === 'note' ? [{ ...trace, id: 'note', type: 'note', title: 'Note de rendez-vous', description: 'Préparer le devis après la séance.', extra_data: '{}', event_deleted: true }] : [trace];
  else if (url.pathname === '/api/memory/drafts') data = { total: 4, items: [
    { id: 'dev', kind: 'devis', title: 'DEV-2026-FICTIF', status: 'draft' }, { id: 'fac', kind: 'facture', title: 'FACT-2026-FICTIF', status: 'draft' },
    { id: 'doc', kind: 'document', title: 'Proposition de formation', status: 'en_cours' }, { id: 'mail', kind: 'email', title: 'Proposition de rendez-vous', status: 'draft' }] };
  else throw new Error('Requête hors scénario local : ' + url.pathname);
  return new Response(JSON.stringify(data), { headers: { 'content-type': 'application/json' } });
};
useDemoStore.setState({ enabled: false });
Object.assign(window, { recetteDemo: (enabled: boolean) => useDemoStore.setState({ enabled }) });
createRoot(document.getElementById('root')!).render(React.createElement(AgentMemoryPanel));
