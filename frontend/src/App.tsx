import { HashRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import SpaceBackground from './components/SpaceBackground';
import Overview from './pages/Overview';
import SpacecraftPage from './pages/Spacecraft';
import TelemetryPage from './pages/Telemetry';
import AnomaliesPage from './pages/Anomalies';
import AIAnalysisPage from './pages/AIAnalysis';
import PredictionsPage from './pages/Predictions';
import SimulationPage from './pages/Simulation';
import MissionLogsPage from './pages/MissionLogs';
import SettingsPage from './pages/Settings';

export default function App() {
  return (
    <HashRouter>
      <SpaceBackground />
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Topbar />
          <main className="flex-1 overflow-y-auto p-4 sm:p-6">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/spacecraft" element={<SpacecraftPage />} />
              <Route path="/telemetry" element={<TelemetryPage />} />
              <Route path="/anomalies" element={<AnomaliesPage />} />
              <Route path="/ai-analysis" element={<AIAnalysisPage />} />
              <Route path="/predictions" element={<PredictionsPage />} />
              <Route path="/simulation" element={<SimulationPage />} />
              <Route path="/mission-logs" element={<MissionLogsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </HashRouter>
  );
}
