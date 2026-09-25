/**
 * B-1429 (recette P-146, lot 1) : la plage d'événements que demande l'Agenda
 * doit couvrir exactement ce que la vue affiche. Elle allait du 1er du mois
 * au dernier jour À MINUIT : le dernier jour était exclu, comme les jours des
 * mois voisins que montre la grille, et la vue Semaine à cheval sur deux mois
 * n'en voyait qu'un.
 *
 * La fin est exclusive (minuit du jour qui suit la dernière case).
 */
export type ModeDeVueAgenda = 'month' | 'week' | 'day' | 'list';

/** Lundi = 0 ; `getDay()` rend 0 pour dimanche (B-247). */
function colonneLundiDabord(date: Date): number {
  return (date.getDay() + 6) % 7;
}

function jour(annee: number, mois: number, quantieme: number): Date {
  return new Date(annee, mois, quantieme);
}

export function plageAffichee(date: Date, mode: ModeDeVueAgenda): { debut: Date; fin: Date } {
  const annee = date.getFullYear();
  const mois = date.getMonth();
  const quantieme = date.getDate();
  if (mode === 'day') {
    return { debut: jour(annee, mois, quantieme), fin: jour(annee, mois, quantieme + 1) };
  }
  if (mode === 'week') {
    const lundi = quantieme - colonneLundiDabord(date);
    return { debut: jour(annee, mois, lundi), fin: jour(annee, mois, lundi + 7) };
  }
  if (mode === 'list') {
    return { debut: jour(annee, mois, 1), fin: jour(annee, mois + 1, 1) };
  }
  // Mois : la grille de 42 cases (six semaines) commence le lundi de la
  // semaine du 1er (CalendarView, MonthView).
  const premier = jour(annee, mois, 1);
  const debutGrille = 1 - colonneLundiDabord(premier);
  return { debut: jour(annee, mois, debutGrille), fin: jour(annee, mois, debutGrille + 42) };
}
