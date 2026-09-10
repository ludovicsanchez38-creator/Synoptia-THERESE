/** Lot 2 DA : la ligne du jour de l'Accueil (date française, sources, heure). */
import type { TodayDashboard } from '../../services/api/dashboard';
import { sourcesPresentes } from './prototypeReadModels';

const FORME_ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

export function formaterLeJour(iso: string): string | null {
  const morceaux = FORME_ISO.exec(iso);
  if (!morceaux) return null;
  const annee = Number(morceaux[1]);
  const mois = Number(morceaux[2]);
  const jour = Number(morceaux[3]);
  const date = new Date(annee, mois - 1, jour);
  const s = new Intl.DateTimeFormat('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(date);
  return s.charAt(0).toLocaleUpperCase('fr-FR') + s.slice(1);
}

export function ligneDuJour(data: TodayDashboard | null, heure: string | null): string {
  const segments: string[] = [];
  if (data) {
    const date = formaterLeJour(data.date);
    if (date) segments.push(date);
    const presentes = sourcesPresentes(data);
    if (presentes.length > 0) {
      segments.push(`Sources : ${presentes.map((s) => s.minuscule).join(', ')}`);
    }
  }
  if (heure) {
    segments.push(`Rafraîchi à ${heure}`);
  }
  return segments.join(' · ');
}
