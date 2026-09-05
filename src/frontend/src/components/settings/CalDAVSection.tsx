/**
 * Calendrier CalDAV — la porte manquante (B-129).
 *
 * Le serveur expose `caldav-test` et `caldav-setup` depuis longtemps, et la
 * création d'un calendrier `provider_type=caldav` répond un 400 qui RENVOIE
 * l'utilisateur vers `caldav-setup`. Aucun fichier de l'interface ne
 * mentionnait ces routes : le message désignait une porte inexistante, et
 * brancher Nextcloud, iCloud ou Radicale était impossible depuis
 * l'application.
 *
 * Cette section ne fait que ça : les identifiants, un essai qui montre ce
 * qu'il a trouvé, un enregistrement qui importe les calendriers découverts.
 * Un échec se voit — il n'est jamais converti en liste vide.
 */
import { useState } from 'react';
import { CalendarCheck } from 'lucide-react';

import { setupCaldavCalendars, testCaldavConnection } from '../../services/api/calendar';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';

interface CalendrierTrouve {
  id: string;
  name: string;
}

export function CalDAVSection() {
  const [url, setUrl] = useState('');
  const [identifiant, setIdentifiant] = useState('');
  const [motDePasse, setMotDePasse] = useState('');
  const [enCours, setEnCours] = useState<'test' | 'enregistrement' | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [trouves, setTrouves] = useState<CalendrierTrouve[] | null>(null);
  const [importes, setImportes] = useState<number | null>(null);

  const identifiantsManquants = !url.trim() || !identifiant.trim() || !motDePasse;

  const credentials = () => ({
    url: url.trim(),
    username: identifiant.trim(),
    password: motDePasse,
  });

  const tester = async () => {
    setEnCours('test');
    setErreur(null);
    setTrouves(null);
    setImportes(null);
    try {
      const resultat = await testCaldavConnection(credentials());
      if (!resultat.success) {
        setErreur(resultat.message || 'La connexion a échoué.');
        return;
      }
      setTrouves(resultat.calendars);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : 'La connexion a échoué.');
    } finally {
      setEnCours(null);
    }
  };

  const enregistrer = async () => {
    setEnCours('enregistrement');
    setErreur(null);
    setImportes(null);
    try {
      const calendriers = await setupCaldavCalendars(credentials());
      setImportes(calendriers.length);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "L'enregistrement a échoué.");
    } finally {
      setEnCours(null);
    }
  };

  return (
    <div className="pt-4 border-t border-border/30">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-sm bg-accent-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
          <CalendarCheck className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-text">Calendrier CalDAV</h3>
          <p className="text-xs text-text-muted">
            Nextcloud, iCloud, Fastmail, cal.com, Radicale, Baikal, Synology…
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <label className="block">
          <span className="text-xs text-text-muted">Adresse du serveur</span>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://cloud.exemple.fr/remote.php/dav"
            autoComplete="off"
            className="mt-1 w-full rounded-sm border border-border bg-surface px-2 py-1.5 text-sm text-text"
          />
        </label>

        <label className="block">
          <span className="text-xs text-text-muted">Identifiant</span>
          <input
            type="text"
            value={identifiant}
            onChange={(e) => setIdentifiant(e.target.value)}
            autoComplete="off"
            className="mt-1 w-full rounded-sm border border-border bg-surface px-2 py-1.5 text-sm text-text"
          />
        </label>

        <label className="block">
          <span className="text-xs text-text-muted">
            Mot de passe (un mot de passe d’application, jamais celui du compte)
          </span>
          <input
            type="password"
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            autoComplete="off"
            className="mt-1 w-full rounded-sm border border-border bg-surface px-2 py-1.5 text-sm text-text"
          />
        </label>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <Button
          variant="ghost"
          onClick={() => void tester()}
          disabled={identifiantsManquants || enCours !== null}
        >
          {enCours === 'test' ? <Spinner taille="bouton" /> : null}
          Tester la connexion
        </Button>
        <Button
          onClick={() => void enregistrer()}
          disabled={identifiantsManquants || enCours !== null}
        >
          {enCours === 'enregistrement' ? <Spinner taille="bouton" /> : null}
          Enregistrer
        </Button>
      </div>

      {erreur && (
        <p role="alert" className="mt-2 text-xs text-error">
          {erreur}
        </p>
      )}

      {trouves && (
        <div className="mt-2 text-xs text-text-muted">
          {trouves.length === 0 ? (
            <p>Connexion établie, mais ce serveur n’expose aucun calendrier.</p>
          ) : (
            <>
              <p className="mb-1">
                Connexion établie. {trouves.length} calendrier
                {trouves.length > 1 ? 's' : ''} trouvé{trouves.length > 1 ? 's' : ''} :
              </p>
              <ul className="list-disc pl-4">
                {trouves.map((calendrier) => (
                  <li key={calendrier.id} className="text-text">
                    {calendrier.name}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {importes === 0 && (
        <p className="mt-2 text-xs text-warning" role="status">
          Connexion établie, mais aucun calendrier n’a été importé : ce serveur n’en expose aucun.
        </p>
      )}
      {importes !== null && importes > 0 && (
        <p className="mt-2 text-xs text-success">
          {importes} calendrier{importes > 1 ? 's' : ''} importé{importes > 1 ? 's' : ''}.
          {importes > 1 ? ' Ils apparaîtront' : ' Il apparaîtra'} à la prochaine
          ouverture de l’Agenda.
        </p>
      )}
    </div>
  );
}
