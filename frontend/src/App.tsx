import React, { useEffect, useState } from 'react';
import type { ObservationPoint, SatelliteCropMeta, StormDetail, StormProfile } from './types';
import { fetchHealth, fetchSatelliteCrops, fetchStormDetail, fetchStorms } from './api';
import { AppHeader } from './components/AppHeader';
import { type ActiveTab, AppNavigation } from './components/AppNavigation';
import { OverviewScreen } from './components/OverviewScreen';
import { SatelliteScreen } from './components/SatelliteScreen';
import { DatasetExplorerScreen } from './components/DatasetExplorerScreen';
import { ForecastLabScreen } from './components/ForecastLabScreen';
import { MethodologyScreen } from './components/MethodologyScreen';
import { AIModelLabScreen } from './components/AIModelLabScreen';
import { AlertCircle, RefreshCw } from 'lucide-react';

const getInitialTab = (): ActiveTab => {
  if (typeof window !== 'undefined' && window.location.hash) {
    const cleanHash = window.location.hash.replace('#', '').toLowerCase();
    if (['overview', 'satellite', 'dataset', 'forecast', 'lab', 'methodology'].includes(cleanHash)) {
      return cleanHash as ActiveTab;
    }
  }
  return 'overview';
};

export const App: React.FC = () => {
  const [activeTab, setActiveTabState] = useState<ActiveTab>(getInitialTab);
  const [storms, setStorms] = useState<StormProfile[]>([]);
  const [selectedStormName, setSelectedStormName] = useState<string>('BIPARJOY');
  const [stormDetail, setStormDetail] = useState<StormDetail | null>(null);
  const [observations, setObservations] = useState<ObservationPoint[]>([]);
  const [selectedObservation, setSelectedObservation] = useState<ObservationPoint | null>(null);
  const [satelliteCrops, setSatelliteCrops] = useState<SatelliteCropMeta[]>([]);
  const [systemConnected, setSystemConnected] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const setActiveTab = (tab: ActiveTab) => {
    setActiveTabState(tab);
    if (typeof window !== 'undefined') {
      window.location.hash = tab;
    }
  };

  useEffect(() => {
    const handleHash = () => {
      const cleanHash = window.location.hash.replace('#', '').toLowerCase();
      if (['overview', 'satellite', 'dataset', 'forecast', 'lab', 'methodology'].includes(cleanHash)) {
        setActiveTabState(cleanHash as ActiveTab);
      }
    };
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  // Initial data loading
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        setError(null);

        const [healthData, stormsData, cropsData] = await Promise.all([
          fetchHealth().catch(() => ({ status: 'OFFLINE' })),
          fetchStorms(),
          fetchSatelliteCrops().catch(() => []),
        ]);

        setSystemConnected(healthData.status === 'OPERATIONAL');
        setStorms(stormsData);
        setSatelliteCrops(cropsData);

        if (stormsData.length > 0) {
          const initialStorm =
            stormsData.find((s) => s.canonical_name === 'BIPARJOY') || stormsData[0];
          setSelectedStormName(initialStorm.canonical_name);
        }
      } catch (err: unknown) {
        console.error('Initialization failed:', err);
        setError(err instanceof Error ? err.message : 'Failed to connect to Vayumarg backend.');
        setSystemConnected(false);
      } finally {
        setLoading(false);
      }
    }

    init();
  }, []);

  // Fetch storm details and chronological track observations when selected storm changes
  useEffect(() => {
    if (!selectedStormName) return;

    fetchStormDetail(selectedStormName)
      .then((detail) => {
        setStormDetail(detail);
        const obsList = detail.observations || [];
        setObservations(obsList);
        if (obsList.length > 0) {
          setSelectedObservation(obsList[obsList.length - 1]);
        } else {
          setSelectedObservation(null);
        }
      })
      .catch((err) => {
        console.error(`Failed to load storm detail for ${selectedStormName}:`, err);
      });
  }, [selectedStormName]);

  const hasSatelliteCrop = satelliteCrops.some(
    (c) => c.storm_name.toUpperCase() === selectedStormName.toUpperCase()
  );

  if (error && storms.length === 0) {
    return (
      <div className="min-h-screen bg-[#0B111B] text-[#EDF3F9] flex flex-col items-center justify-center p-6">
        <div className="max-w-md w-full bg-[#111B28] border border-[#D86F6F]/40 p-6 rounded-lg text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-[#D86F6F] mx-auto" />
          <h2 className="text-base font-bold text-[#EDF3F9]">Vayumarg Operational Backend Unavailable</h2>
          <p className="text-xs text-[#96A8BB] leading-relaxed">
            Could not connect to the operational Vayumarg FastAPI service at <code className="text-[#61BACB]">http://127.0.0.1:8000</code>.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-[#172333] hover:bg-[#1D2B3D] border border-[#1E2E42] text-[#EDF3F9] text-xs font-semibold rounded flex items-center justify-center gap-2 mx-auto cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Connection</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0B111B] text-[#EDF3F9]">
      {/* Top Application Header */}
      <AppHeader
        storms={storms}
        selectedStormName={selectedStormName}
        onSelectStorm={(name) => setSelectedStormName(name)}
        systemConnected={systemConnected}
        hasSatelliteCrop={hasSatelliteCrop}
      />

      {/* Main Workspace: Left Sidebar + Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigation */}
        <AppNavigation
          activeTab={activeTab}
          onSelectTab={(tab) => setActiveTab(tab)}
          hasSatelliteCrop={hasSatelliteCrop}
        />

        {/* Dynamic Route Content */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {activeTab === 'overview' && (
            <OverviewScreen
              stormDetail={stormDetail}
              observations={observations}
              selectedObservation={selectedObservation}
              onSelectObservation={(obs) => setSelectedObservation(obs)}
              onNavigateToSatellite={() => setActiveTab('satellite')}
              onNavigateToForecast={() => setActiveTab('forecast')}
              isLoading={loading}
              hasSatelliteCrop={hasSatelliteCrop}
            />
          )}

          {activeTab === 'satellite' && (
            <SatelliteScreen
              storms={storms}
              selectedStormName={selectedStormName}
              onSelectStorm={(name) => setSelectedStormName(name)}
              satelliteCrops={satelliteCrops}
            />
          )}

          {activeTab === 'dataset' && <DatasetExplorerScreen />}

          {activeTab === 'forecast' && (
            <ForecastLabScreen
              storms={storms}
              selectedStormName={selectedStormName}
              onSelectStorm={(name) => setSelectedStormName(name)}
              stormDetail={stormDetail}
              observations={observations}
            />
          )}

          {activeTab === 'lab' && (
            <AIModelLabScreen
              onNavigateToForecast={() => setActiveTab('forecast')}
              onNavigateToSatellite={() => setActiveTab('satellite')}
            />
          )}

          {activeTab === 'methodology' && <MethodologyScreen />}
        </main>
      </div>
    </div>
  );
};

export default App;
