/**
 * Libellés et icônes des statuts de pièce. Source unique pour les filtres
 * du panneau ; plus de couleur ni de pastille.
 */
import {
  ArrowRightLeft,
  Ban,
  CheckCircle2,
  Clock,
  FileText,
  Mail,
  ThumbsDown,
  AlertCircle,
  type LucideIcon,
} from 'lucide-react';

export const STATUS_CONFIG: Record<string, { label: string; icon: LucideIcon }> = {
  draft: { label: 'Brouillon', icon: FileText },
  sent: { label: 'Envoyée', icon: Mail },
  accepted: { label: 'Accepté', icon: CheckCircle2 },
  refused: { label: 'Refusé', icon: ThumbsDown },
  expired: { label: 'Expiré', icon: Clock },
  paid: { label: 'Payée', icon: CheckCircle2 },
  overdue: { label: 'En retard', icon: AlertCircle },
  converted: { label: 'Converti', icon: ArrowRightLeft },
  cancelled: { label: 'Annulée', icon: Ban },
};
