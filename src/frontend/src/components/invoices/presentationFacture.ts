/**
 * Présentation de la liste Devis et factures (dates, compteur, trois colonnes).
 * Module sans composant (fast refresh).
 */
import type { Invoice } from '../../services/api';
import type { TonEtiquette } from '../ui/Etiquette';
import { STATUS_CONFIG } from './statutsFacture';

export function dateListe(iso: string): string {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function sousLignePiece(invoice: Invoice): string {
  if (invoice.document_type === 'devis') return 'Devis';
  if (invoice.document_type === 'avoir') return 'Avoir';
  // `Intl.DateTimeFormat().format()` LÈVE `RangeError: Invalid time value` sur
  // une date invalide, là où `toLocaleDateString` rendait « Invalid Date ».
  // Appelée pour chaque rangée, une seule `issue_date` hors norme emportait
  // le panneau entier dans le GlobalErrorBoundary (scénario B-010).
  const d = new Date(invoice.issue_date);
  if (Number.isNaN(d.getTime())) return 'Facture';
  const mois = d.toLocaleDateString('fr-FR', { month: 'long' });
  return `Facture · ${mois}`;
}

export function compteurPieces(n: number, tronquee: boolean, echues: number): string {
  const s = n > 1 ? 's' : '';
  let texte = `${n}${tronquee ? '+' : ''} pièce${s}`;
  if (echues === 1) texte += ', dont 1 pièce échue';
  else if (echues > 1) texte += `, dont ${echues} pièces échues`;
  return texte;
}

export type CelluleEnvoi = {
  ton: TonEtiquette;
  texte: string;
  sous?: string;
  icone?: boolean;
};

export type CellulePaiement =
  | { ton: TonEtiquette; texte: string }
  | { texte: 'Sans objet' };

export type CelluleEcheance = {
  texte: string;
  echue?: boolean;
  muted?: boolean;
  sous?: string;
};

function masculin(type: Invoice['document_type'] | undefined): boolean {
  return type === 'devis' || type === 'avoir';
}

export function cellulesStatut(invoice: Invoice): {
  envoi: CelluleEnvoi;
  paiement: CellulePaiement;
  echeance: CelluleEcheance;
} {
  const issue = dateListe(invoice.issue_date);
  const due = dateListe(invoice.due_date);
  const envoye = masculin(invoice.document_type) ? `Envoyé le ${issue}` : `Envoyée le ${issue}`;
  const emis = masculin(invoice.document_type) ? `Émis le ${issue}` : `Émise le ${issue}`;

  if (!STATUS_CONFIG[invoice.status]) {
    return {
      envoi: { ton: 'neutre', texte: invoice.status, icone: true },
      paiement: { texte: 'Sans objet' },
      echeance: { texte: due, muted: true },
    };
  }

  if (invoice.status === 'draft') {
    return {
      envoi: { ton: 'neutre', texte: 'Brouillon', sous: emis },
      paiement: { texte: 'Sans objet' },
      echeance: {
        texte: due,
        muted: true,
        sous:
          invoice.document_type === 'devis' && invoice.validite_jours
            ? `Validité : ${invoice.validite_jours} jours`
            : undefined,
      },
    };
  }

  if (invoice.status === 'cancelled') {
    return {
      envoi: { ton: 'neutre', texte: masculin(invoice.document_type) ? 'Annulé' : 'Annulée' },
      paiement: { texte: 'Sans objet' },
      echeance: { texte: due, muted: true },
    };
  }

  if (invoice.document_type === 'devis') {
    const paiement: CellulePaiement =
      invoice.status === 'sent'
        ? { ton: 'neutre', texte: "En attente d'accord" }
        : invoice.status === 'accepted'
          ? { ton: 'succes', texte: 'Accepté' }
          : invoice.status === 'refused'
            ? { ton: 'attention', texte: 'Refusé' }
            : invoice.status === 'expired'
              ? { ton: 'attention', texte: 'Expiré' }
              : invoice.status === 'converted'
                ? { ton: 'neutre', texte: 'Converti' }
                : { texte: 'Sans objet' };
    return {
      envoi: { ton: 'info', texte: envoye },
      paiement,
      echeance: { texte: `Valable jusqu'au ${due}` },
    };
  }

  const avoir = invoice.document_type === 'avoir';
  if (invoice.status === 'paid') {
    const date = invoice.payment_date ? dateListe(invoice.payment_date) : null;
    const texte = avoir
      ? date
        ? `Payé le ${date}`
        : 'Payé'
      : date
        ? `Payée le ${date}`
        : 'Payée';
    return {
      envoi: { ton: 'info', texte: envoye },
      paiement: { ton: 'succes', texte },
      echeance: { texte: due, muted: true },
    };
  }

  if (invoice.status === 'overdue') {
    return {
      envoi: { ton: 'info', texte: envoye },
      paiement: { ton: 'erreur', texte: avoir ? 'Impayé' : 'Impayée' },
      echeance: { texte: `${due} · échue`, echue: true },
    };
  }

  if (invoice.status === 'sent') {
    return {
      envoi: { ton: 'info', texte: envoye },
      paiement: { ton: 'attention', texte: avoir ? 'Impayé' : 'Impayée' },
      echeance: { texte: due },
    };
  }

  // Couple type/statut non décrit par le tableau du design (une facture ou un
  // avoir `accepted`, `refused`, `expired`, `converted` : statuts présents en
  // base, non filtrables hors devis). Affirmer un impayé mentirait ; on replie
  // sur le libellé réel du statut, en ton neutre.
  return {
    envoi: { ton: 'info', texte: envoye },
    paiement: { ton: 'neutre', texte: STATUS_CONFIG[invoice.status].label },
    echeance: { texte: due },
  };
}
