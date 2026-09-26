/**
 * Les prestations d'une personne (tranche C du 29/08).
 *
 * Une liste, pas un tableau à colonnes : une personne peut avoir une vente
 * en cours de livraison et une autre en proposition. Et une étape s'écrit en
 * toutes lettres — la campagne des dix personas a assez dit ce que valent
 * « des petits dessins sans nom ».
 *
 * P-132 : les étapes sont celles du pipeline (six des huit : ni Contact ni
 * Actif, qui décrivent une personne), avec les mots des colonnes.
 */

import { useCallback, useEffect, useId, useState } from 'react';
import {
  changerLaPhase,
  creerUnePrestation,
  listerLesPrestations,
  type PhaseDePrestation,
  type Prestation,
} from '../../services/api/prestations';
import { ETAPES_DE_PRESTATION } from './pipelineEtapes';

function montantLisible(montant: number | null): string {
  // Absent n'est pas zéro : afficher 0,00 € affirmerait que c'est gratuit.
  if (montant === null || montant === undefined) return 'Montant non renseigné';
  return `${montant.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} € HT`;
}

function estUneEtapeDePrestation(valeur: string): boolean {
  return ETAPES_DE_PRESTATION.some((etape) => etape.id === valeur);
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
  const [phase, setPhase] = useState<PhaseDePrestation>('discovery');
  const idEtape = useId();

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
    setPhase('discovery');
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
                {/* Le selecteur EST l'affichage de l'etape : la repeter en
                    dessous donnait deux fois le meme mot a l'ecran. */}
                <select
                  aria-label={`Étape de ${p.intitule}`}
                  className="rounded-sm border border-border bg-surface-2 px-2 py-1 text-sm text-text"
                  value={p.phase}
                  onChange={(e) => basculer(p.id, e.target.value as PhaseDePrestation)}
                >
                  {/* P-132 : une valeur que le pipeline ne connaît pas se dit
                      telle quelle ; sans cette option, le sélecteur
                      afficherait la première étape à sa place. */}
                  {!estUneEtapeDePrestation(p.phase) && (
                    <option value={p.phase} disabled>
                      Étape inconnue : {p.phase}
                    </option>
                  )}
                  {ETAPES_DE_PRESTATION.map((etape) => (
                    <option key={etape.id} value={etape.id}>
                      {etape.label}
                    </option>
                  ))}
                </select>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Revue du diff P-132, constat 5 : dans la fiche, « Étape » nomme déjà
          le contrôle qui change l'étape du contact, dès le choix. Celui-ci ne
          fait que préparer une prestation : il est groupé et nommé à part. */}
      <fieldset className="m-0 min-w-0 border-0 p-0">
        <legend className="sr-only">Nouvelle prestation</legend>
        <div className="flex flex-wrap items-end gap-2 border-t border-border pt-3">
          <label className="text-xs text-text-muted">
            Intitulé
            <input
              className="mt-1 block rounded-sm border border-border bg-surface px-2 py-1 text-sm text-text"
              value={intitule}
              onChange={(e) => setIntitule(e.target.value)}
              placeholder="Accompagnement mensuel, audit, formation…"
            />
          </label>
          <div className="text-xs text-text-muted">
            {/* P-132 : le mot de la fiche, « Étape », plutôt que « Où ça en est ». */}
            <label htmlFor={idEtape}>
              Étape<span className="sr-only"> de la nouvelle prestation</span>
            </label>
            <select
              id={idEtape}
              className="mt-1 block rounded-sm border border-border bg-surface px-2 py-1 text-sm text-text"
              value={phase}
              onChange={(e) => setPhase(e.target.value as PhaseDePrestation)}
            >
              {ETAPES_DE_PRESTATION.map((etape) => (
                <option key={etape.id} value={etape.id}>
                  {etape.label}
                </option>
              ))}
            </select>
          </div>
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
      </fieldset>
    </div>
  );
}
