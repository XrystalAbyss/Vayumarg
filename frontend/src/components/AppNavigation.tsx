import React from 'react';
import { LayoutDashboard, Satellite, Target, BookOpen, ShieldCheck, Database, Cpu } from 'lucide-react';

export type ActiveTab = 'overview' | 'satellite' | 'dataset' | 'forecast' | 'lab' | 'methodology';

interface AppNavigationProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
  hasSatelliteCrop: boolean;
}

export const AppNavigation: React.FC<AppNavigationProps> = ({
  activeTab,
  onSelectTab,
  hasSatelliteCrop,
}) => {
  const navItems: { id: ActiveTab; label: string; icon: React.FC<{ className?: string }>; badge?: string }[] = [
    {
      id: 'overview',
      label: 'Overview',
      icon: LayoutDashboard,
    },
    {
      id: 'satellite',
      label: 'Satellite Ops',
      icon: Satellite,
      badge: hasSatelliteCrop ? 'MULTICHANNEL' : undefined,
    },
    {
      id: 'dataset',
      label: 'Satellite Dataset',
      icon: Database,
      badge: '4 CROPS',
    },
    {
      id: 'forecast',
      label: 'Forecast Lab',
      icon: Target,
      badge: '+6/12/24h',
    },
    {
      id: 'lab',
      label: 'AI Model Lab',
      icon: Cpu,
      badge: 'VERIFIED',
    },
    {
      id: 'methodology',
      label: 'Methodology',
      icon: BookOpen,
    },
  ];

  return (
    <aside className="w-56 bg-[#111B28] border-r border-[#1E2E42] flex flex-col justify-between py-4 select-none shrink-0">
      <div className="space-y-1 px-3">
        <div className="px-3 pb-2 text-[10px] font-bold text-[#96A8BB] uppercase tracking-wider">
          Studio Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#1D2B3D] text-[#EDF3F9] border-l-2 border-[#61BACB] shadow-sm'
                  : 'text-[#96A8BB] hover:text-[#EDF3F9] hover:bg-[#172333]'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? 'text-[#61BACB]' : 'text-[#96A8BB]'
                  }`}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`px-1.5 py-0.5 text-[9px] rounded font-semibold ${
                    isActive
                      ? 'bg-[#61BACB]/20 text-[#61BACB]'
                      : 'bg-[#172333] text-[#96A8BB]'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Operational Metadata Info */}
      <div className="px-4 pt-4 border-t border-[#1E2E42] text-[11px] text-[#96A8BB] space-y-2">
        <div className="flex items-center gap-1.5 text-[#61BACB] font-semibold text-xs">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>WMO / IMD Standards</span>
        </div>
        <p className="text-[10px] leading-relaxed text-[#96A8BB]/80">
          Strict separation between historical ground-truth fixes, physical IR analytics, and forward trajectory baselines.
        </p>
        <div className="text-[9px] text-[#96A8BB]/50 pt-1 font-mono">
          VAYUMARG CORE v2.0-STABLE
        </div>
      </div>
    </aside>
  );
};
