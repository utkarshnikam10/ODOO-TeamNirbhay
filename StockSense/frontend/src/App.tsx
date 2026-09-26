import React, { useState } from 'react';
import { InventoryProvider, useInventory } from './context/InventoryContext';
import { Sidebar } from './components/common/Sidebar';
import { Header } from './components/common/Header';
import { DemoFlowBar } from './components/common/DemoFlowBar';
import { ToastContainer } from './components/common/Toast';

import { AuthView } from './views/AuthView';
import { DashboardView } from './views/DashboardView';
import { ProductsView } from './views/ProductsView';
import { ReceiptsView } from './views/ReceiptsView';
import { DeliveriesView } from './views/DeliveriesView';
import { TransfersView } from './views/TransfersView';
import { AdjustmentsView } from './views/AdjustmentsView';
import { LedgerView } from './views/LedgerView';
import { WarehousesView } from './views/WarehousesView';
import { ProfileView } from './views/ProfileView';

const MainAppContent: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
  const { activeView } = useInventory();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView />;
      case 'products':
        return <ProductsView />;
      case 'receipts':
        return <ReceiptsView />;
      case 'deliveries':
        return <DeliveriesView />;
      case 'transfers':
        return <TransfersView />;
      case 'adjustments':
        return <AdjustmentsView />;
      case 'ledger':
        return <LedgerView />;
      case 'warehouses':
        return <WarehousesView />;
      case 'profile':
        return <ProfileView onLogoutClick={onLogout} />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 font-sans selection:bg-sky-100 selection:text-sky-900">
      {/* Hackathon Interactive Demo Flow Runner */}
      <DemoFlowBar />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          isMobileOpen={isMobileSidebarOpen}
          setIsMobileOpen={setIsMobileSidebarOpen}
          onLogoutClick={onLogout}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <Header
            onMobileMenuToggle={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
            onLogoutClick={onLogout}
          />

          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
            {renderActiveView()}
          </main>
        </div>
      </div>

      <ToastContainer />
    </div>
  );
};

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);

  if (!isAuthenticated) {
    return <AuthView onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <InventoryProvider>
      <MainAppContent onLogout={() => setIsAuthenticated(false)} />
    </InventoryProvider>
  );
}

export default App;
