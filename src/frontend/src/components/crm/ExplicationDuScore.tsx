/**
 * P-152 : l'explication du score, lisible au clavier.
 *
 * Elle vivait dans le `title` d'une icône SVG : ni focalisable, ni lue au
 * clavier, et générale. Un vrai bouton la déplie ; sur une fiche, elle dit
 * aussi le motif du dernier changement (activité `score_change`, présentée
 * comme dans la frise, B-1421).
 */
import { useEffect, useId, useState } from 'react';
import { HelpCircle } from 'lucide-react';

import { presenterActivite } from '../../lib/activitesCrm';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { listActivities } from '../../services/api/crm-extended';
import { SCORE_AIDE } from './pipelineEtapes';

export function ExplicationDuScore({ contactId }: { contactId?: string }) {
  const [ouverte, setOuverte] = useState(false);
  const [dernierChangement, setDernierChangement] = useState<string | null>(null);
  const idExplication = useId();

  useEffect(() => {
    if (!ouverte) return;
    return pushEscapeHandler(() => setOuverte(false));
  }, [ouverte]);

  useEffect(() => {
    if (!ouverte || !contactId) return;
    let vivant = true;
    listActivities({ contact_id: contactId, type: 'score_change', limit: 1 })
      .then((activites) => {
        if (!vivant) return;
        const derniere = activites[0];
        if (!derniere) { setDernierChangement(null); return; }
        const { titre, description } = presenterActivite(derniere);
        setDernierChangement([titre, description].filter(Boolean).join(' · '));
      })
      .catch(() => { if (vivant) setDernierChangement(null); });
    return () => { vivant = false; };
  }, [ouverte, contactId]);

  return (
    <>
      <button
        type="button"
        aria-label="Expliquer le score"
        aria-expanded={ouverte}
        aria-controls={idExplication}
        // Dans une carte du Pipeline : le clic ouvrirait la fiche et Entrée
        // ou Espace lanceraient un glisser (même garde que « Ouvrir la fiche »).
        onClick={(e) => { e.stopPropagation(); setOuverte((v) => !v); }}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') e.stopPropagation(); }}
        className="inline-grid h-6 w-6 place-items-center rounded-sm text-text-muted hover:text-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <HelpCircle className="h-4 w-4" aria-hidden />
      </button>
      {ouverte && (
        <span id={idExplication} className="block basis-full text-xs font-normal leading-5 text-text-muted">
          {SCORE_AIDE}
          {dernierChangement && <span className="block">Dernier changement : {dernierChangement}</span>}
        </span>
      )}
    </>
  );
}
