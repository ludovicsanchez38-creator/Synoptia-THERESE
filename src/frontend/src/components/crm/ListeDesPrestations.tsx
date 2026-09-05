/**
 * Les prestations d'une personne (tranche C du 29/08).
 *
 * Une liste, pas un tableau à colonnes : le Kanban des contacts a sept étapes
 * qui ne parlent que de vente, alors que Ludo suit aussi ce qui est en cours
 * de livraison. Et une phase s'écrit en toutes lettres — la campagne des dix
 * personas a assez dit ce que valent « des petits dessins sans nom ».
 */

import { useCallback, useEffect, useState } from 'react';
import {
  LIBELLE_DE_PHASE,
  PHASES_DE_PRESTATION,
  changerLaPhase,
  creerUnePrestation,
  listerLesPrestations,
  type PhaseDePrestation,
  type Prestation,
} from '../../services/api/prestations';

function montantLisible(montant: number | null): string {
  // Absent n'est pas zéro : afficher 0,00 € affirmerait que c'est gratuit.
  if (montant === null || montant === undefined) return 'Montant non renseigné';
  return `${montant.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} € HT`;
}

export function ListeDesPrestations({ contactId }: { contactId: string }) {
  const [prestations, setPrestations] = useState<Prestation[]>([]);
  const [chargement, setChargement] = useState(true);
  // Une panne n'est pas un vide : sans ce message, l'écran affirmait
  // « Aucune prestation » alors que le serveur n'avait pas répondu (05/09/2026).
  const [erreur, setErreur] = useState<string | null>(null);
  const [intitule, setIntitule] = useState('');
  const [montant, setMontant] = useState('');
  // Aucun defaut cache : l'application ne choisit pas l'etape a la place de
  // qui travaille (« une fuite sous un lavabo n'est pas une piste »). Le
  // choix est a l'ecran, et il part avec la creation.
  const [phase, setPhase] = useState<PhaseDePrestation>('piste');

  const recharger = useCallback(async () => {
    setChargement(true);
    try {
      setPrestations(await listerLesPrestations(contactId));
      setErreur(null);
    } catch {
      setErreur('Impossible de charger les prestations. Réessaie dans un instant.');
    } finally {
      setChargement(false);
    }
  }, [contactId]);

  useEffect(() => {
    void recharger();
  }, [recharger]);

  async function ajouter() {
    const nom = intitule.trim();
    // Une prestation sans nom serait une ligne vide que Ludo devrait deviner.
    if (!nom) return;
    const brut = montant.trim().replace(',', '.');
    await creerUnePrestation({
      contact_id: contactId,
      intitule: nom,
      montant_ht: brut ? Number(brut) : null,
      // Obligatoire cote API depuis la 0.59 : l'omettre rendait le bouton
      // « Ajouter » inoperant, sans que rien ne le dise.
      phase,
    });
    setIntitule('');
    setMontant('');
    setPhase('piste');
    await recharger();
  }

  async function basculer(id: string, phase: PhaseDePrestation) {
    await changerLaPhase(id, phase);
    await recharger();
  }

  return (
    <div className="space-y-3">
      {chargement ? (
        <p className="text-sm text-text-muted">Lecture des prestations…</p>
      ) : erreur ? (
        <p role="alert" className="text-sm text-error-ink">{erreur}</p>
      ) : prestations.length === 0 ? (
        <p className="text-sm text-text-muted">
          Aucune prestation enregistrée pour cette personne.
        </p>
      ) : (
        <ul className="space-y-2">
          {prestations.map((p) => (
            <li key={p.id} className="rounded-md border border-border bg-surface p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-text">{p.intitule}</p>
                  <p className="text-xs text-text-muted">{montantLisible(p.montant_ht)}</p>
                </div>
                <label className="text-xs">
                  {/* Le selecteur EST l'affichage de la phase : la repeter
                      en dessous donnait deux fois le meme mot a l'ecran. */}
                  <span className="sr-only">Phase de {p.intitule}</span>
                  <select
                    className="rounded-sm border border-border bg-surface-2 px-2 py-1 text-sm text-text"
                    value={p.phase}
                    onChange={(e) => basculer(p.id, e.target.value as PhaseDePrestation)}
                  >
                    {PHASES_DE_PRESTATION.map((phase) => (
                      <option key={phase} value={phase}>
                        {LIBELLE_DE_PHASE[phase]}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap items-end gap-2 border-t border-border pt-3">
        <label className="text-xs text-text-muted">
          Intitulé
          <input
            className="mt-1 block rounded-sm border border-border bg-surface px-2 py-1 text-sm text-text"
            value={intitule}
            onChange={(e) => setIntitule(e.target.value)}
            placeholder="FORGER, PROPULSER, diagnostic…"
          />
        </label>
        <label className="text-xs text-text-muted">
          Où ça en est
          <select
            className="mt-1 block rounded-sm border border-border bg-surface px-2 py-1 text-sm text-text"
            value={phase}
            onChange={(e) => setPhase(e.target.value as PhaseDePrestation)}
          >
            {PHASES_DE_PRESTATION.map((p) => (
              <option key={p} value={p}>
                {LIBELLE_DE_PHASE[p]}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-text-muted">
          Montant HT (facultatif)
          <input
            className="mt-1 block w-32 rounded-sm border border-border bg-surface px-2 py-1 text-sm text-text"
            value={montant}
            onChange={(e) => setMontant(e.target.value)}
            inputMode="decimal"
          />
        </label>
        <button
          type="button"
          onClick={ajouter}
          className="rounded-sm bg-accent px-3 py-1.5 text-sm font-medium text-ink-on-fill"
        >
          Ajouter
        </button>
      </div>
    </div>
  );
}
