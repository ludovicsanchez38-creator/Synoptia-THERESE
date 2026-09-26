/**
 * P-148 : ce que rassemble un projet, en tête de sa fenêtre. Quatre lignes
 * (Conversations, Documents, Tâches, Contacts) nourries par une seule
 * lecture, `GET /api/memory/projects/{id}/ensemble` : un seul état de
 * chargement, et une famille illisible se dit sur sa ligne au lieu d'un zéro.
 *
 * Aucun geste de création ici : chaque famille a déjà le sien, que le texte
 * du vide nomme.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

import { lireLEnsembleDuProjet, type EnsembleDuProjet } from '../../services/api';
import type { DestinationDuTravail } from '../../lib/destinationDuTravail';
import { formatRelativeDate } from '../../lib/utils';
import { useDemoMask } from '../../hooks/useDemoMask';
import { VueDEnsemble, type EtatDeLEnsemble, type FamilleDEnsemble } from '../ui/VueDEnsemble';

const LIMITE_COURTE = 5;
const LIMITE_LONGUE = 200;

type Depliable = 'conversations' | 'documents' | 'contacts';

function pluriel(n: number, singulier: string, plurielDuMot: string): string {
  return `${n} ${n > 1 ? plurielDuMot : singulier}`;
}

/** « 2026-09-20T12:00:00 » -> « 20 sept. » : le jour décidé, sans conversion de fuseau. */
function jourDEcheance(echeance: string): string {
  const [annee, mois, jour] = echeance.slice(0, 10).split('-').map(Number);
  return new Date(annee, mois - 1, jour).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

function detailDeTache(statut: string, echeance: string | null, enRetard: boolean): string {
  if (statut === 'done') return 'Terminée';
  if (statut === 'cancelled') return 'Annulée';
  if (!echeance) return 'Sans échéance';
  return enRetard ? `En retard, échéance ${jourDEcheance(echeance)}` : `Échéance ${jourDEcheance(echeance)}`;
}

export function ProjectEnsembleSection({
  projectId,
  masquer = (texte: string) => texte,
  onMener,
}: {
  projectId: string;
  /** Le masque de la fenêtre : il ne révèle rien tant que les contacts ne sont pas lus. */
  masquer?: (texte: string) => string;
  /**
   * Mène à la destination d'un élément (lot 3). Les liens restent actifs en
   * démonstration : ils mènent en lecture, comme partout.
   */
  onMener?: (cible: DestinationDuTravail) => void;
}) {
  const { maskContact } = useDemoMask();
  const [ensemble, setEnsemble] = useState<EnsembleDuProjet | null>(null);
  const [etat, setEtat] = useState<EtatDeLEnsemble>('chargement');
  const [limite, setLimite] = useState(LIMITE_COURTE);
  const [deplies, setDeplies] = useState<ReadonlySet<Depliable>>(new Set());
  const [relecture, setRelecture] = useState(false);
  const requeteRef = useRef(0);
  // La ligne dépliée reprend le focus quand son bouton disparaît.
  const [focusApres, setFocusApres] = useState<Depliable | null>(null);
  const prefixe = `projet-${projectId.replace(/[^a-zA-Z0-9-]/g, '')}`;

  const lire = useCallback(async (lim: number) => {
    const requete = ++requeteRef.current;
    try {
      const lu = await lireLEnsembleDuProjet(projectId, lim);
      if (requete !== requeteRef.current) return;
      setEnsemble(lu);
      setEtat('pret');
    } catch {
      if (requete !== requeteRef.current) return;
      setEtat('panne');
    } finally {
      if (requete === requeteRef.current) setRelecture(false);
    }
  }, [projectId]);

  useEffect(() => {
    setEnsemble(null);
    setEtat('chargement');
    setLimite(LIMITE_COURTE);
    setDeplies(new Set());
    setFocusApres(null);
    void lire(LIMITE_COURTE);
    return () => { requeteRef.current += 1; };
  }, [lire]);

  const focalisee = useCallback(() => setFocusApres(null), []);

  const reessayer = useCallback(() => {
    setEtat('chargement');
    void lire(limite);
  }, [lire, limite]);

  const deplier = useCallback((famille: Depliable) => {
    setDeplies((courants) => new Set([...courants, famille]));
    setFocusApres(famille);
    if (limite < LIMITE_LONGUE) {
      setLimite(LIMITE_LONGUE);
      setRelecture(true);
      void lire(LIMITE_LONGUE);
    }
  }, [lire, limite]);

  function visibles<T>(famille: Depliable, elements: T[]): T[] {
    return deplies.has(famille) ? elements : elements.slice(0, LIMITE_COURTE);
  }

  function gesteEtComplet(famille: Depliable, total: number, affiches: number, phraseIncomplete: string) {
    if (!deplies.has(famille)) {
      return total > affiches
        ? { action: { libelle: `Tout afficher (${total})`, onClick: () => deplier(famille), enCours: relecture } }
        : {};
    }
    return total > affiches ? { incomplete: phraseIncomplete } : {};
  }

  const e = ensemble;
  const familles: FamilleDEnsemble[] = [];

  const conversations = e?.conversations ? visibles('conversations', e.conversations.elements) : [];
  familles.push({
    cle: 'conversations',
    libelle: 'Conversations',
    total: e ? (e.conversations?.total ?? null) : 0,
    elements: conversations.map((c) => {
      const titre = masquer(c.titre || 'Conversation sans titre');
      return {
        id: c.id, libelle: titre, detail: formatRelativeDate(c.mise_a_jour),
        nomAccessible: `Ouvrir la conversation ${titre}`,
        onOuvrir: onMener && (() => onMener({ kind: 'conversation', id: c.id })),
      };
    }),
    texteDuVide: 'Aucune conversation rattachée. Une conversation se rattache depuis son sélecteur de projet.',
    ...(e?.conversations ? gesteEtComplet('conversations', e.conversations.total, conversations.length,
      `Liste incomplète : les ${conversations.length} plus récentes sont affichées.`) : {}),
  });

  const documents = e?.documents ? visibles('documents', e.documents.elements) : [];
  familles.push({
    cle: 'documents',
    libelle: 'Documents',
    total: e ? (e.documents?.total ?? null) : 0,
    elements: documents.map((d) => {
      const titre = masquer(d.titre);
      return {
        id: d.id, libelle: titre, detail: d.statut === 'termine' ? 'Terminé' : 'En cours',
        nomAccessible: `Ouvrir le document ${titre}`,
        onOuvrir: onMener && (() => onMener({ kind: 'document', id: d.id })),
      };
    }),
    texteDuVide: 'Aucun document. Un document se rattache à un projet à sa création.',
    ...(e?.documents ? gesteEtComplet('documents', e.documents.total, documents.length,
      `Liste incomplète : les ${documents.length} plus récents sont affichés.`) : {}),
  });

  const taches = e?.taches ?? null;
  familles.push({
    cle: 'taches',
    libelle: 'Tâches',
    total: e ? (taches?.total ?? null) : 0,
    resume: taches
      ? taches.ouvertes === 0
        ? 'Aucune ouverte'
        : `${pluriel(taches.ouvertes, 'ouverte', 'ouvertes')}${taches.en_retard > 0 ? `, dont ${taches.en_retard} en retard` : ''}`
      : undefined,
    // Une tâche seule ne s'ouvre pas depuis le bus : l'élément reste un texte,
    // et le geste mène à toutes les tâches du projet, dans Tâches.
    elements: (taches?.elements ?? []).slice(0, LIMITE_COURTE).map((t) => ({
      id: t.id,
      libelle: masquer(t.titre),
      detail: detailDeTache(t.statut, t.echeance, t.en_retard),
    })),
    texteDuVide: 'Aucune tâche. Une tâche se rattache à un projet depuis son formulaire.',
    ...(taches && taches.total > 0 && onMener
      ? {
          action: {
            libelle: taches.total > 1 ? `Voir les ${taches.total} tâches dans Tâches` : 'Voir la tâche dans Tâches',
            onClick: () => onMener({ kind: 'taches-du-projet', projetId: projectId }),
          },
        }
      : {}),
  });

  const contacts = e?.contacts ? visibles('contacts', e.contacts.elements) : [];
  familles.push({
    cle: 'contacts',
    libelle: 'Contacts',
    total: e ? (e.contacts?.total ?? null) : 0,
    elements: contacts.map((c) => {
      // Revue P-148, constat 2 : maskContact champ par champ, comme le
      // sélecteur « Contact associé ». Le masque de texte de la fenêtre ne
      // connaît que les contacts lus : un contact rangé absent du carnet
      // sortait en clair.
      const fiche = maskContact(c);
      const nomComplet = [fiche.first_name, fiche.last_name].filter(Boolean).join(' ');
      const nom = nomComplet || fiche.company || 'Contact sans nom';
      const entreprise = nomComplet ? fiche.company : null;
      return {
        id: c.id,
        libelle: nom,
        detail: c.associe ? 'Contact associé' : entreprise || 'Rangé dans ce projet',
        nomAccessible: `Ouvrir la fiche de ${nom}`,
        onOuvrir: onMener && (() => onMener({ kind: 'contact', id: c.id })),
      };
    }),
    texteDuVide: 'Aucun contact associé : choisis-le plus bas, dans Informations du projet.',
    ...(e?.contacts ? gesteEtComplet('contacts', e.contacts.total, contacts.length,
      `Liste incomplète : ${contacts.length} contacts affichés sur ${e.contacts.total}.`) : {}),
  });

  return (
    <VueDEnsemble
      prefixe={prefixe}
      etat={etat}
      familles={familles}
      onReessayer={reessayer}
      messageDePanne="Ce que rassemble ce projet n’a pas pu être lu."
      messageDeChargement="Lecture de ce que rassemble ce projet…"
      focaliser={focusApres && !relecture ? focusApres : null}
      onFocalise={focalisee}
    />
  );
}
