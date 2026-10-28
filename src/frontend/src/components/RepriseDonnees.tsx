import { useEffect, useState } from 'react';
import { initializeAuth, request } from '../services/api/core';
import { Button } from './ui/Button';
import { DialogShell } from './ui/DialogShell';

type Copie = { id: string; date: string; version: string };
const dateCopie = (copie: Copie) => new Date(copie.date).toLocaleString('fr-FR');

export function RepriseDonnees({ onRestart }: { onRestart: () => Promise<void> | void }) {
  const [copies, setCopies] = useState<Copie[] | null>(null);
  const [choix, setChoix] = useState<Copie | null>(null);
  const [occupe, setOccupe] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [abri, setAbri] = useState<string | null>(null);
  const [lecture, setLecture] = useState(0);
  useEffect(() => {
    let actif = true;
    setErreur(null);
    void initializeAuth().then(() => request<{ copies: Copie[] }>('/api/reprise/copies'))
      .then((resultat) => { if (actif) setCopies(resultat.copies); })
      .catch(() => { if (actif) setErreur('La liste des copies n’a pas pu être lue. Réessaie.'); });
    return () => { actif = false; };
  }, [lecture]);

  async function restaurer() {
    if (!choix || occupe) return;
    setOccupe(true);
    setErreur(null);
    try {
      const resultat = await request<{ base_mise_de_cote: string }>('/api/reprise/restaurer', {
        method: 'POST', body: JSON.stringify({ copie: choix.id, confirmer: true }), timeoutMs: 0,
      });
      setAbri(resultat.base_mise_de_cote);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : 'La restauration a échoué. Tu peux réessayer.');
    } finally {
      setOccupe(false);
      setChoix(null);
    }
  }

  return <main className="h-screen overflow-y-auto bg-bg text-text p-8">
    <div className="max-w-xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Récupérer tes données</h1>
      <p>THÉRÈSE n’a pas pu ouvrir les données ou terminer leur mise à jour.</p>
      <p>Tu peux revenir à une copie automatique. La base actuelle sera mise de côté avant la restauration, avec ses fichiers associés.</p>
      {erreur && <p role="alert" className="text-error">{erreur}</p>}
      {abri ? <>
        <p role="status">La copie a été restaurée. Redémarre le moteur pour la charger.</p>
        <p className="break-all">Base précédente conservée dans : {abri}</p>
        <Button onClick={() => void onRestart()}>Redémarrer le moteur</Button>
      </> : <>
        {copies === null && !erreur && <p role="status">Lecture des copies…</p>}
        {copies?.length === 0 && <p>Aucune copie automatique disponible. Si tu as une sauvegarde manuelle, conserve-la avec ton dossier de données pour être accompagné dans la récupération.</p>}
        {copies && copies.length > 0 && <>
          <p className="text-sm text-text-muted">La version indiquée est celle du moteur qui a créé la copie, avant la mise à jour des données.</p>
          <ul className="space-y-3">{copies.map((copie) => <li key={copie.id} className="border border-border rounded p-3 space-y-2">
            <p>{dateCopie(copie)} · Version {copie.version}</p>
            <Button disabled={occupe} onClick={() => setChoix(copie)}>Restaurer cette copie du {dateCopie(copie)}</Button>
          </li>)}</ul>
        </>}
        {erreur && copies === null && <Button onClick={() => setLecture((n) => n + 1)}>Relire les copies</Button>}
        <Button disabled={occupe} variant="ghost" onClick={() => void onRestart()}>Réessayer le démarrage</Button>
      </>}
    </div>
    <DialogShell open={choix !== null} ariaLabel="Confirmer la restauration" onClose={() => { if (!occupe) setChoix(null); }} className="max-w-lg bg-bg p-6 rounded-lg space-y-4">
      <h2 className="text-xl">Restaurer cette copie ?</h2>
      {choix && <p>{dateCopie(choix)} · Version {choix.version}</p>}
      <p>Les changements faits après cette copie ne seront plus dans la base active. La base actuelle et ses fichiers associés seront conservés dans le dossier backups/reprises.</p>
      <p>Les documents et l’index de recherche ne sont pas restaurés par ces copies de la base.</p>
      <Button disabled={occupe} onClick={() => setChoix(null)}>Annuler</Button>
      <Button disabled={occupe} onClick={() => void restaurer()}>{occupe ? 'Restauration en cours…' : 'Confirmer la restauration'}</Button>
    </DialogShell>
  </main>;
}
