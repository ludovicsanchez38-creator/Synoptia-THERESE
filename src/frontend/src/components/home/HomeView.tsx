/**
 * THÉRÈSE v2 - HomeView : vue Accueil hybride (lanceur + journée).
 * Compose les sous-composants ; charge /today + /setup-status en parallèle.
 */
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { fetchTodayDashboard, fetchSetupStatus, type TodayDashboard, type SetupStatus } from '../../services/api/dashboard';
import { HomeHeader } from './HomeHeader';
import { QuickActions } from './QuickActions';
import { RecentConversations } from './RecentConversations';
import { TodayPanels } from './TodayPanels';
import { SetupChecklist } from './SetupChecklist';

export function HomeView() {
  const [today, setToday] = useState<TodayDashboard | null>(null);
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [todayError, setTodayError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchTodayDashboard().then((d) => !cancelled && setToday(d)).catch(() => !cancelled && setTodayError(true));
    fetchSetupStatus().then((s) => !cancelled && setSetup(s)).catch(() => { /* bande masquée si indispo */ });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="flex-1 min-w-0 overflow-y-auto px-7 py-5">
      <div className="flex flex-col gap-[18px] max-w-[1100px] mx-auto">
        <HomeHeader />
        {setup && <SetupChecklist status={setup} />}
        <QuickActions />
        <RecentConversations />

        {today ? (
          <TodayPanels data={today} />
        ) : todayError ? (
          <p className="text-sm text-text-muted">Aperçu du jour indisponible pour le moment.</p>
        ) : (
          <div className="flex items-center justify-center gap-2 py-8 text-sm text-text-muted">
            <Loader2 className="w-5 h-5 animate-spin text-accent" /> Chargement de ta journée…
          </div>
        )}
      </div>
    </div>
  );
}
