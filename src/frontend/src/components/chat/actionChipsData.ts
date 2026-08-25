/**
 * Les puces d'actions déterministes du chat - données (panel 0.48 : module
 * séparé du composant pour l'export vers le test de lexique, react-refresh
 * exigeant qu'un fichier composant n'exporte que des composants).
 */
import { Mail, Users, FileText, FileSpreadsheet } from 'lucide-react';

export const CHIPS = [
  { label: "Ouvrir l'email", insert: '{action: ouvrir email}', Icon: Mail },
  { label: 'Ouvrir le Pipeline', insert: '{action: ouvrir pipeline}', Icon: Users },
  {
    label: 'Document Word',
    insert: '{action: produire docx "sujet du document"}',
    Icon: FileText,
  },
  {
    label: 'Tableur Excel',
    insert: '{action: produire xlsx "sujet du tableur"}',
    Icon: FileSpreadsheet,
  },
] as const;
