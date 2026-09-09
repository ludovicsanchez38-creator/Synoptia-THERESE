/**
 * P-049 (Sophie sophie-06, B-634 ; accepté par Ludo le 08/09/2026).
 *
 * Renseigner les variables inconnues d'un prompt sans quitter le composeur.
 * Le formulaire ENREGISTRE des variables (`createVariable`), il ne réécrit
 * jamais le message : les directives `[contact: …]` du message sont analysées
 * AVANT la résolution des variables (`routers/chat.py`), donc une valeur
 * injectée dans le texte deviendrait une commande (revue COCO, finding 1).
 * Les jetons restent dans le message et le moteur les résout au bon endroit.
 *
 * Enregistrement par champ (finding 3) : chaque succès ou refus est marqué
 * sur sa ligne, une saisie refusée est conservée, rien n'est remplacé
 * automatiquement. Échap se consomme ici (finding 5) : il ferme le formulaire
 * et rend le focus au composeur, sans remonter à la cascade de l'application.
 */
import { useEffect, useRef, useState } from 'react';

import { createVariable } from '../../services/api/variables';

type EtatChamp = { valeur: string; statut: 'saisie' | 'enregistree' | 'refusee'; erreur: string | null };

export function FormulaireVariables({
  inconnues,
  onEnregistre,
  onFermer,
}: {
  /** Noms des jetons inconnus, dans l'ordre du message. */
  inconnues: string[];
  /** Au moins une variable a été enregistrée : le parent recalcule son aperçu. */
  onEnregistre: () => void;
  onFermer: () => void;
}) {
  const [champs, setChamps] = useState<Record<string, EtatChamp>>(() =>
    Object.fromEntries(inconnues.map((nom) => [nom, { valeur: '', statut: 'saisie', erreur: null }])),
  );
  const [enCours, setEnCours] = useState(false);
  const premierRef = useRef<HTMLInputElement>(null);

  useEffect(() => { premierRef.current?.focus(); }, []);
  // Revue COCO 0.69.0 (finding 4) : le parent ne remonte plus le formulaire
  // à chaque aperçu (un succès partiel effaçait les saisies refusées) ; les
  // jetons apparus depuis reçoivent leur champ, les autres gardent leur état.
  useEffect(() => {
    setChamps((courants) => {
      const manquants = inconnues.filter((nom) => !courants[nom]);
      if (manquants.length === 0) return courants;
      return { ...courants, ...Object.fromEntries(manquants.map((nom) => [nom, { valeur: '', statut: 'saisie', erreur: null }])) };
    });
  }, [inconnues]);

  const noms = inconnues.filter((nom) => champs[nom]);
  const aRemplir = noms.filter((nom) => champs[nom].statut !== 'enregistree' && champs[nom].valeur.trim());

  const enregistrer = async () => {
    if (enCours || aRemplir.length === 0) return;
    setEnCours(true);
    let succes = 0;
    for (const nom of aRemplir) {
      try {
        await createVariable(nom, 'text', champs[nom].valeur.trim());
        succes += 1;
        setChamps((c) => ({ ...c, [nom]: { ...c[nom], statut: 'enregistree', erreur: null } }));
      } catch (err) {
        const message = err instanceof Error && err.message ? err.message : 'Enregistrement refusé.';
        setChamps((c) => ({ ...c, [nom]: { ...c[nom], statut: 'refusee', erreur: message } }));
      }
    }
    setEnCours(false);
    if (succes > 0) onEnregistre();
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      onFermer();
    }
  };

  const refus = noms.filter((nom) => champs[nom].statut === 'refusee');

  return (
    <div
      role="group"
      aria-label="Renseigner les variables"
      data-testid="formulaire-variables"
      onKeyDown={onKeyDown}
      className="mb-2 rounded-md border border-border/60 bg-surface-elevated/60 p-3 text-xs"
    >
      <p className="text-text-muted">
        Ces valeurs deviennent des variables réutilisables ; le message garde ses jetons et le moteur les remplace à l'envoi.
      </p>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        {noms.map((nom, index) => {
          const champ = champs[nom];
          const id = `variable-${nom}`;
          return (
            <label key={nom} htmlFor={id} className="block font-semibold text-text">
              {`{${nom}}`}
              <input
                id={id}
                ref={index === 0 ? premierRef : undefined}
                value={champ.valeur}
                disabled={enCours || champ.statut === 'enregistree'}
                aria-invalid={champ.statut === 'refusee' || undefined}
                onChange={(event) => setChamps((c) => ({ ...c, [nom]: { valeur: event.target.value, statut: 'saisie', erreur: null } }))}
                className="mt-1 w-full rounded-md border border-border bg-surface px-2 py-1.5 font-normal text-text"
              />
              {champ.statut === 'enregistree' && <span className="mt-1 block font-normal text-success">{`{${nom}}`} enregistrée</span>}
            </label>
          );
        })}
      </div>
      {refus.length > 0 && (
        <div role="alert" className="mt-2 rounded-md border border-error/40 bg-[var(--color-error-tint)] px-2 py-1.5 text-error">
          {refus.map((nom) => `{${nom}} : ${champs[nom].erreur}`).join(' · ')}
        </div>
      )}
      <div className="mt-2 flex justify-end gap-2">
        <button type="button" onClick={onFermer} className="rounded-md border border-border px-2.5 py-1 text-sm font-semibold text-text-muted">Fermer</button>
        <button type="button" onClick={() => void enregistrer()} disabled={enCours || aRemplir.length === 0} className="rounded-md bg-accent-fill px-2.5 py-1 text-sm font-semibold text-accent-ink disabled:opacity-40">
          {enCours ? 'Enregistrement…' : 'Enregistrer comme variables'}
        </button>
      </div>
    </div>
  );
}
