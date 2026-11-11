import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { DrugSearchPage } from './pages/DrugSearchPage';
import { DrugAssistantPage } from './pages/DrugAssistantPage';
import { InteractionExplorerPage } from './pages/InteractionExplorerPage';
import { KnowledgeGraphPage } from './pages/KnowledgeGraphPage';
import { LiteratureExplorerPage } from './pages/LiteratureExplorerPage';
import { EvaluationDashboardPage } from './pages/EvaluationDashboardPage';
import { UserHistoryPage } from './pages/UserHistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { AuthPage } from './pages/AuthPage';
import { PageId, HealthResponse } from './types';
import { fetchHealth } from './services/api';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('landing');
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.error('Health fetch error:', err);
    }
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onNavigate={setCurrentPage} />;
      case 'dashboard':
        return <DashboardPage health={health} onNavigate={setCurrentPage} />;
      case 'drug-search':
        return <DrugSearchPage />;
      case 'assistant':
        return <DrugAssistantPage />;
      case 'interactions':
        return <InteractionExplorerPage />;
      case 'graph':
        return <KnowledgeGraphPage />;
      case 'literature':
        return <LiteratureExplorerPage />;
      case 'evaluation':
        return <EvaluationDashboardPage />;
      case 'history':
        return <UserHistoryPage onNavigate={setCurrentPage} />;
      case 'settings':
        return <SettingsPage health={health} />;
      case 'auth':
        return <AuthPage onNavigate={setCurrentPage} />;
      default:
        return <LandingPage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500 selection:text-white">
      <Navbar currentPage={currentPage} onNavigate={setCurrentPage} health={health} />

      <div className="flex-1 flex flex-col md:flex-row max-w-7xl w-full mx-auto">
        <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-x-hidden">
          {renderPage()}
        </main>
      </div>

      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>PharmaMind AI v1.0.0 • Biomedical NLP & Knowledge Graph System</span>
          <span>Educational and Informational Use Only • Strict Provenance Protocol</span>
        </div>
      </footer>
    </div>
  );
};

export default App;

