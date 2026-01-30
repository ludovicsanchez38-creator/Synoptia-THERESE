/**
 * THÉRÈSE v2 - Activity Timeline (CRM Phase 5)
 *
 * Timeline des activités d'un contact.
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Phone, Users, FileText, TrendingUp, ArrowRight, Clock } from 'lucide-react';
import { listActivities, type ActivityResponse } from '../../services/api';

interface ActivityTimelineProps {
  contactId: string;
}

const ACTIVITY_ICONS = {
  email: Mail,
  call: Phone,
  meeting: Users,
  note: FileText,
  stage_change: ArrowRight,
  score_change: TrendingUp,
};

const ACTIVITY_COLORS = {
  email: 'text-blue-400',
  call: 'text-green-400',
  meeting: 'text-purple-400',
  note: 'text-yellow-400',
  stage_change: 'text-cyan-400',
  score_change: 'text-magenta-400',
};

export function ActivityTimeline({ contactId }: ActivityTimelineProps) {
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActivities();
  }, [contactId]);

  const loadActivities = async () => {
    try {
      setLoading(true);
      const data = await listActivities({ contact_id: contactId, limit: 50 });
      setActivities(data);
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins}min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;

    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-cyan"></div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8 text-text-muted">
        <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>Aucune activité pour ce contact</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activities.map((activity, index) => {
        const Icon = ACTIVITY_ICONS[activity.type as keyof typeof ACTIVITY_ICONS] || FileText;
        const color = ACTIVITY_COLORS[activity.type as keyof typeof ACTIVITY_COLORS] || 'text-text-muted';

        return (
          <motion.div
            key={activity.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex gap-4"
          >
            {/* Timeline line */}
            <div className="relative flex flex-col items-center">
              <div className={`${color} bg-surface rounded-full p-2`}>
                <Icon className="w-4 h-4" />
              </div>
              {index < activities.length - 1 && (
                <div className="w-0.5 h-full bg-surface mt-2"></div>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 pb-6">
              <div className="bg-surface rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-text-primary">{activity.title}</h4>
                  <span className="text-xs text-text-muted whitespace-nowrap ml-2">
                    {formatDate(activity.created_at)}
                  </span>
                </div>

                {activity.description && (
                  <p className="text-sm text-text-muted">{activity.description}</p>
                )}

                {activity.extra_data && (
                  <div className="mt-2 text-xs text-text-muted opacity-70">
                    {activity.extra_data}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
