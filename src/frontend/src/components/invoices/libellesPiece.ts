/** B-1038 : un devis n'est pas une « facture » dans les messages. */
export function libellesDeLaPiece(type: string | null | undefined): { cree: string; misAJour: string; nom: string; nomDefini: string } {
  if (type === 'devis') return { cree: 'Devis créé', misAJour: 'Devis mis à jour', nom: 'devis', nomDefini: 'le devis' };
  if (type === 'avoir') return { cree: 'Avoir créé', misAJour: 'Avoir mis à jour', nom: 'avoir', nomDefini: 'l’avoir' };
  return { cree: 'Facture créée', misAJour: 'Facture mise à jour', nom: 'facture', nomDefini: 'la facture' };
}
