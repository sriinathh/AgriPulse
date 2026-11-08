import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { LandingPage } from './pages/LandingPage';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { FarmersPage } from './pages/FarmersPage';
import { FieldsPage } from './pages/FieldsPage';
import { CropsPage } from './pages/CropsPage';
import { SensorsPage } from './pages/SensorsPage';
import { ReadingsPage } from './pages/ReadingsPage';
import { WeatherPage } from './pages/WeatherPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { ProfilePage } from './pages/ProfilePage';
import { IrrigationSchedulePage } from './pages/IrrigationSchedulePage';

export function App() {
  return (
    <>
      <Routes>
        {/* Full-width Landing Page */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/signin" element={<AuthPage />} />
        <Route path="/signup" element={<AuthPage />} />

        {/* Dashboard and Management Pages inside Sidebar Layout */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/schedules" element={<IrrigationSchedulePage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/farmers" element={<FarmersPage />} />
          <Route path="/fields" element={<FieldsPage />} />
          <Route path="/crops" element={<CropsPage />} />
          <Route path="/sensors" element={<SensorsPage />} />
          <Route path="/readings" element={<ReadingsPage />} />
          <Route path="/weather" element={<WeatherPage />} />
          <Route path="/data-quality" element={<DataQualityPage />} />
          <Route path="/status" element={<SystemStatusPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}

export default App;
