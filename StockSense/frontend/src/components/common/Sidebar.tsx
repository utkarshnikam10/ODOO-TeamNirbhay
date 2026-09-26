import React from 'react';
import {
  LayoutDashboard,
  Package,
  ArrowDownLeft,
  ArrowUpRight,
  ArrowRightLeft,
  SlidersHorizontal,
  History,
  Warehouse,
  User,
  LogOut,
  Boxes,
  ChevronRight,
  RotateCcw,
} from 'lucide-react';
import { useInventory } from '../../context/InventoryContext';
import { ViewType } from '../../types';

interface SidebarProps {
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
  onLogoutClick: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isMobileOpen, setIsMobileOpen, onLogoutClick }) => {
  const { activeView, setActiveView, resetToDefaultData } = useInventory();

  const handleNav = (view: ViewType) => {
    setActiveView(view);
    setIsMobileOpen(false);
  };

  const navItemClass = (view: ViewType) =>
    `flex items-center gap-2.5 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
      activeView === view
        ? 'bg-sky-700 text-white shadow-xs font-semibold'
        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
    }`;

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Shell */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:static lg:translate-x-0 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo Section */}
        <div className="flex h-14 items-center justify-between border-b border-slate-200 px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-700 text-white shadow-xs">
              <Boxes className="h-5 w-5" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-slate-900">StockSense</span>
              <span className="ml-1 rounded-xs bg-slate-100 px-1 py-0.5 text-[10px] font-semibold text-slate-500 uppercase">
                ERP v2.4
              </span>
            </div>
          </div>
        </div>

        {/* Nav Links */}
        <div className="flex-1 overflow-y-auto p-3 space-y-6">
          <div>
            <button onClick={() => handleNav('dashboard')} className={`w-full ${navItemClass('dashboard')}`}>
              <LayoutDashboard className="h-4 w-4" />
              <span>Dashboard</span>
            </button>

            <button onClick={() => handleNav('products')} className={`w-full mt-1 ${navItemClass('products')}`}>
              <Package className="h-4 w-4" />
              <span>Products & Stock</span>
            </button>
          </div>

          {/* Operations Group */}
          <div>
            <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Operations
            </div>
            <div className="mt-1 space-y-0.5">
              <button onClick={() => handleNav('receipts')} className={`w-full ${navItemClass('receipts')}`}>
                <ArrowDownLeft className="h-4 w-4 text-emerald-600" />
                <span>Receipts (Incoming)</span>
              </button>

              <button onClick={() => handleNav('deliveries')} className={`w-full ${navItemClass('deliveries')}`}>
                <ArrowUpRight className="h-4 w-4 text-blue-600" />
                <span>Delivery Orders</span>
              </button>

              <button onClick={() => handleNav('transfers')} className={`w-full ${navItemClass('transfers')}`}>
                <ArrowRightLeft className="h-4 w-4 text-amber-600" />
                <span>Internal Transfers</span>
              </button>

              <button onClick={() => handleNav('adjustments')} className={`w-full ${navItemClass('adjustments')}`}>
                <SlidersHorizontal className="h-4 w-4 text-purple-600" />
                <span>Inventory Adjustments</span>
              </button>

              <button onClick={() => handleNav('ledger')} className={`w-full ${navItemClass('ledger')}`}>
                <History className="h-4 w-4 text-slate-500" />
                <span>Stock Ledger / History</span>
              </button>
            </div>
          </div>

          {/* Settings Group */}
          <div>
            <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Settings & Control
            </div>
            <div className="mt-1 space-y-0.5">
              <button onClick={() => handleNav('warehouses')} className={`w-full ${navItemClass('warehouses')}`}>
                <Warehouse className="h-4 w-4" />
                <span>Warehouses</span>
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-slate-200 p-3 bg-slate-50/50 space-y-2">
          <button
            onClick={() => handleNav('profile')}
            className={`w-full flex items-center justify-between rounded-md p-2 text-xs text-slate-700 hover:bg-slate-200/60 transition-colors ${
              activeView === 'profile' ? 'bg-slate-200/80 font-semibold' : ''
            }`}
          >
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-sky-100 border border-sky-300 flex items-center justify-center text-sky-800 font-bold text-xs">
                VS
              </div>
              <div className="text-left">
                <div className="font-semibold text-slate-900 leading-tight">Vikramjit Singh</div>
                <div className="text-[10px] text-slate-500">Operations Manager</div>
              </div>
            </div>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
          </button>

          <div className="flex items-center justify-between gap-1 pt-1">
            <button
              onClick={resetToDefaultData}
              className="flex-1 flex items-center justify-center gap-1 rounded-md border border-slate-200 bg-white py-1.5 text-[11px] font-medium text-slate-600 hover:bg-slate-100 transition-colors"
              title="Reset system demo state"
            >
              <RotateCcw className="h-3 w-3" />
              Reset Demo
            </button>
            <button
              onClick={onLogoutClick}
              className="flex items-center justify-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-3 py-1.5 text-[11px] font-medium text-rose-700 hover:bg-rose-100 transition-colors"
              title="Sign out of application"
            >
              <LogOut className="h-3 w-3" />
              Logout
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
