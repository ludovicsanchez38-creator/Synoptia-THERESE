/**
 * Libellés des statuts de pièce. Source unique pour les filtres du panneau ;
 * plus de couleur, plus de pastille, et plus d'icône : personne ne la lisait
 * (l'icône du statut inconnu est un `FileText` posé par le composant).
 */
export const STATUS_CONFIG: Record<string, { label: string }> = {
  draft: { label: 'Brouillon' },
  sent: { label: 'Envoyée' },
  accepted: { label: 'Accepté' },
  refused: { label: 'Refusé' },
  expired: { label: 'Expiré' },
  paid: { label: 'Payée' },
  overdue: { label: 'En retard' },
  converted: { label: 'Converti' },
  cancelled: { label: 'Annulée' },
};


export function libelleStatutPiece(statut: string, type: string): string {
  const feminin = type === 'facture';
  const accords: Record<string, string> = {
    sent: feminin ? 'Envoyée' : 'Envoyé',
    paid: feminin ? 'Payée' : 'Payé',
    cancelled: feminin ? 'Annulée' : 'Annulé',
  };
  return accords[statut] ?? STATUS_CONFIG[statut]?.label ?? statut;
}
