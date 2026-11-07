import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import AircraftListPage from './pages/AircraftListPage';
import AddAircraftPage from './pages/AddAircraftPage';
import AircraftDetailsPage from './pages/AircraftDetailsPage';
import EngineMonitoringPage from './pages/EngineMonitoringPage';
import PredictiveMaintenancePage from './pages/PredictiveMaintenancePage';
import MaintenancePage from './pages/MaintenancePage';

function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Determine navbar title based on active path
  const getPageTitle = (pathname) => {
    if (pathname === '/') return 'Executive Fleet Dashboard';
    if (pathname.startsWith('/aircraft/add')) return 'Register Aircraft';
    if (pathname.startsWith('/aircraft/')) return 'Aircraft Diagnostics & Profile';
    if (pathname.startsWith('/aircraft')) return 'Fleet Assets Management';
    if (pathname.startsWith('/monitoring')) return 'Turbofan Telemetry Stream';
    if (pathname.startsWith('/predictive')) return 'Predictive Maintenance & RUL Inference';
    if (pathname.startsWith('/maintenance')) return 'Maintenance Work Order Management';
    return 'AeroPredict Platform';
  };

  return (
    <div className="app-container">
      {/* Aviation Navigation Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="main-content">
        <Navbar
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          activeTitle={getPageTitle(location.pathname)}
        />

        <main className="mt-4">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/aircraft" element={<AircraftListPage />} />
            <Route path="/aircraft/add" element={<AddAircraftPage />} />
            <Route path="/aircraft/:id" element={<AircraftDetailsPage />} />
            <Route path="/monitoring" element={<EngineMonitoringPage />} />
            <Route path="/predictive" element={<PredictiveMaintenancePage />} />
            <Route path="/maintenance" element={<MaintenancePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
