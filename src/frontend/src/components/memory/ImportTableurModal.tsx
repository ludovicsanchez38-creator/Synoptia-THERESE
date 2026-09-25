/**
 * P-130 (persona Nathalie, cycle 13) : importer un tableur de contacts (CSV,
 * Excel ou JSON). Le moteur savait prévisualiser et importer, avec les
 * colonnes reconnues et les lignes écartées ; aucun écran ne l'appelait, et
 * « Importer (.vcf) » refusait le fichier de Nathalie.
 *
 * Trois temps : choisir le fichier, lire l'aperçu (rien n'est encore écrit),
 * importer puis lire le résultat.
 */
import { useEffect, useRef, useState } from 'react';
import { AlertCircle, FileSpreadsheet, X } from 'lucide-react';
import * as api from '../../services/api';
import type { ApercuImportContacts, LigneDImport, ResultatImportContacts } from '../../services/api';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { Z_LAYER } from '../../styles/z-layers';

const CHAMPS: Record<string, string> = {
  id: 'Identifiant',
  first_name: 'Prénom',
  last_name: 'Nom',
  company: 'Entreprise',
  email: 'E-mail',
  phone: 'Téléphone',
  address: 'Adresse',
  notes: 'Notes',
  tags: 'Tags',
  stage: 'Étape',
  source: 'Source',
  score: 'Score',
  scope: 'Périmètre',
  next_follow_up: 'Prochaine relance',
};

function nomDuChamp(champ: string): string {
  return CHAMPS[champ] ?? champ;
}

/** B-1442 : le moteur numérote depuis la première ligne de DONNÉES. Dans un
 *  CSV ou un classeur, l'en-tête occupe la ligne 1 : on affiche le numéro que
 *  l'utilisateur voit dans son tableur. Dans un JSON, c'est le rang. */
function texteDeLaLigne(ligne: LigneDImport, fichier: File | null): string {
  if (ligne.row <= 0) return ligne.message;
  if (fichier?.name.toLowerCase().endsWith('.json')) return `Élément ${ligne.row} : ${ligne.message}`;
  return `Ligne ${ligne.row + 1} du tableur : ${ligne.message}`;
}

export function ImportTableurModal({ onFermer, onImporte }: { onFermer: () => void; onImporte: () => void }) {
  const fenetreRef = useRef<HTMLDivElement>(null);
  const [fichier, setFichier] = useState<File | null>(null);
  const [apercu, setApercu] = useState<ApercuImportContacts | null>(null);
  const [resultat, setResultat] = useState<ResultatImportContacts | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  useDialogFocusTrap(fenetreRef, { active: true, isolateBackground: true });
  // Échap ferme cette fenêtre, pas la vue Contacts dessous (pile d'Échap,
  // interceptée avant le retour de vue de la coque, comme les fenêtres de
  // suppression et RGPD du panneau). Pendant un envoi, il ne ferme rien.
  const enCoursRef = useRef(false);
  enCoursRef.current = enCours;
  const onFermerRef = useRef(onFermer);
  onFermerRef.current = onFermer;
  useEffect(() => pushEscapeHandler(() => {
    if (!enCoursRef.current) onFermerRef.current();
  }), []);

  async function lireLAperçu(choisi: File) {
    setFichier(choisi);
    setApercu(null);
    setResultat(null);
    setErreur(null);
    setEnCours(true);
    try {
      setApercu(await api.apercuImportContacts(choisi));
    } catch (err) {
      setErreur(err instanceof Error && err.message ? err.message : 'Le fichier n’a pas pu être lu.');
    } finally {
      setEnCours(false);
    }
  }

  async function importer() {
    if (!fichier) return;
    setEnCours(true);
    setErreur(null);
    try {
      setResultat(await api.importerContactsTableur(fichier));
      onImporte();
    } catch (err) {
      setErreur(err instanceof Error && err.message ? err.message : 'L’import a échoué ; rien n’a été confirmé.');
    } finally {
      setEnCours(false);
    }
  }

  const reconnues = apercu ? Object.entries(apercu.column_mapping) : [];
  const ignorees = apercu ? apercu.detected_columns.filter((colonne) => !(colonne in apercu.column_mapping)) : [];

  return (
    <div className={`fixed inset-0 flex items-center justify-center bg-text/35 p-4 ${Z_LAYER.MODAL}`}>
      <div
        ref={fenetreRef}
        role="dialog"
        aria-modal="true"
        aria-label="Importer des contacts depuis un tableur"
        aria-busy={enCours}
        tabIndex={-1}
        className="flex max-h-[calc(100dvh-2rem)] w-full max-w-xl flex-col overflow-hidden rounded-md border border-border bg-surface shadow-lg"
      >
        <div className="flex shrink-0 items-center gap-3 border-b border-border px-4 py-3">
          <FileSpreadsheet className="h-5 w-5 text-text-muted" aria-hidden="true" />
          <h2 className="flex-1 text-base font-semibold text-text">Importer un tableur de contacts</h2>
          <Button type="button" variant="ghost" size="icon" onClick={onFermer} disabled={enCours} aria-label="Fermer l’import">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4 text-sm text-text">
          {!resultat && (
            <div>
              <label htmlFor="import-tableur-fichier" className="block font-medium">
                Choisir un fichier (CSV, Excel ou JSON)
              </label>
              <input
                id="import-tableur-fichier"
                type="file"
                accept=".csv,.xlsx,.xls,.json,text/csv,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                disabled={enCours}
                onChange={(event) => {
                  const choisi = event.target.files?.[0];
                  if (choisi) void lireLAperçu(choisi);
                }}
                className="mt-1 block w-full text-sm text-text-muted file:mr-3 file:rounded-sm file:border file:border-border file:bg-surface-2 file:px-3 file:py-1.5 file:text-sm file:text-text"
              />
              <p className="mt-1 text-sm text-text-muted">
                Rien n’est enregistré avant « Importer » : l’aperçu dit d’abord ce qui sera repris.
              </p>
            </div>
          )}

          {enCours && (
            <p role="status" className="flex items-center gap-2 text-text-muted">
              <Spinner taille="ligne" /> {apercu ? 'Import en cours…' : 'Lecture du fichier…'}
            </p>
          )}

          {erreur && <Alerte icone={<AlertCircle className="h-4 w-4" />}>{erreur}</Alerte>}

          {apercu && !resultat && (
            <div className="space-y-3">
              <p className="font-medium">{apercu.total_rows} {apercu.total_rows > 1 ? 'lignes lues.' : 'ligne lue.'}</p>
              {reconnues.length > 0 && (
                <div>
                  <p className="font-medium">Colonnes reconnues</p>
                  <ul className="mt-1 list-disc pl-5 text-text-muted">
                    {reconnues.map(([source, champ]) => <li key={source}>{source} → {nomDuChamp(champ)}</li>)}
                  </ul>
                </div>
              )}
              {ignorees.length > 0 && (
                <p className="text-text-muted">
                  <span className="font-medium text-text">Colonnes ignorées :</span> {ignorees.join(', ')}
                </p>
              )}
              {apercu.validation_errors.length > 0 && (
                <div>
                  <p className="font-medium">Lignes écartées ou signalées</p>
                  <ul className="mt-1 list-disc pl-5 text-text-muted">
                    {apercu.validation_errors.map((ligne, i) => <li key={`${ligne.row}-${i}`}>{texteDeLaLigne(ligne, fichier)}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {resultat && (
            <div className="space-y-2" role="status">
              {/* Les chiffres une seule fois : le message du moteur les répétait. */}
              <p className="font-medium">
                Import terminé : {resultat.created} créé{resultat.created > 1 ? 's' : ''}, {resultat.updated} mis à jour, {resultat.skipped} écarté{resultat.skipped > 1 ? 's' : ''}.
              </p>
              {resultat.errors.length > 0 && <p className="font-medium">Lignes signalées</p>}
              {resultat.errors.length > 0 && (
                <ul className="list-disc pl-5 text-text-muted">
                  {resultat.errors.map((ligne, i) => <li key={`${ligne.row}-${i}`}>{texteDeLaLigne(ligne, fichier)}</li>)}
                </ul>
              )}
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap justify-end gap-2 border-t border-border bg-surface-2 px-4 py-3">
          {resultat ? (
            <Button type="button" variant="primary" size="md" onClick={onFermer}>Fermer</Button>
          ) : (
            <>
              <Button type="button" variant="ghost" size="md" onClick={onFermer} disabled={enCours}>Annuler</Button>
              {apercu?.can_import && (
                <Button type="button" variant="primary" size="md" onClick={() => void importer()} disabled={enCours}>
                  {`Importer ${apercu.total_rows} ${apercu.total_rows > 1 ? 'lignes' : 'ligne'}`}
                </Button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
