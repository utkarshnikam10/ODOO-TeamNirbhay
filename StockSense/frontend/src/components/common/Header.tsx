import React, { useState, useRef, useEffect } from 'react';
import {
  Menu,
  Search,
  Bell,
  User as UserIcon,
  LogOut,
  Package,
  ArrowRight,
  CheckCheck,
  ChevronDown,
  Warehouse,
  FileText,
} from 'lucide-react';
import { useInventory } from '../../context/InventoryContext';
import { ViewType } from '../../types';

interface HeaderProps {
  onMobileMenuToggle: () => void;
  onLogoutClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMobileMenuToggle, onLogoutClick }) => {
  const {
    activeView,
    setActiveView,
    notifications,
    markNotificationRead,
    markAllNotificationsRead,
    products,
    receipts,
    deliveries,
    currentUser,
  } = useInventory();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const unreadNotifCount = notifications.filter((n) => !n.read).length;

  // Handle clicking outside dropdowns
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setIsNotifOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter search results
  const searchProducts = searchQuery.trim()
    ? products.filter(
        (p) =>
          p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.category.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 5)
    : [];

  const searchReceipts = searchQuery.trim()
    ? receipts.filter(
        (r) =>
          r.receiptNo.toLowerCase().includes(searchQuery.toLowerCase()) ||
          r.supplier.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 3)
    : [];

  const searchDeliveries = searchQuery.trim()
    ? deliveries.filter(
        (d) =>
          d.deliveryNo.toLowerCase().includes(searchQuery.toLowerCase()) ||
          d.customer.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 3)
    : [];

  const hasSearchResults =
    searchProducts.length > 0 || searchReceipts.length > 0 || searchDeliveries.length > 0;

  // Get Breadcrumbs title
  const getBreadcrumb = () => {
    switch (activeView) {
      case 'dashboard':
        return { title: 'Dashboard', path: 'Overview' };
      case 'products':
        return { title: 'Products & Stock Inventory', path: 'Catalog' };
      case 'receipts':
        return { title: 'Goods Receipts (Incoming)', path: 'Operations' };
      case 'deliveries':
        return { title: 'Delivery Orders (Outgoing)', path: 'Operations' };
      case 'transfers':
        return { title: 'Internal Stock Transfers', path: 'Operations' };
      case 'adjustments':
        return { title: 'Inventory Adjustments', path: 'Operations' };
      case 'ledger':
        return { title: 'Stock Ledger / Move History', path: 'Audit Log' };
      case 'warehouses':
        return { title: 'Warehouse Management', path: 'Settings' };
      case 'profile':
        return { title: 'User Profile & Preferences', path: 'Account' };
      default:
        return { title: 'Dashboard', path: 'Overview' };
    }
  };

  const breadcrumb = getBreadcrumb();

  return (
    <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur-xs">
      {/* Left: Mobile Menu Button & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMobileMenuToggle}
          className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 lg:hidden"
          title="Toggle Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400">{breadcrumb.path}</span>
          <span className="text-slate-300">/</span>
          <span className="font-semibold text-slate-900">{breadcrumb.title}</span>
        </div>
      </div>

      {/* Right Controls: Search, Notifications, Profile */}
      <div className="flex items-center gap-3">
        {/* Global Search Bar */}
        <div ref={searchRef} className="relative hidden sm:block w-64 md:w-80">
          <div className="relative flex items-center">
            <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search SKU, Product, Receipt, Delivery..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setIsSearchOpen(true);
              }}
              onFocus={() => setIsSearchOpen(true)}
              className="w-full rounded-md border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-800 placeholder-slate-400 focus:border-sky-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500 transition-colors"
            />
          </div>

          {/* Search Dropdown Results */}
          {isSearchOpen && searchQuery.trim() !== '' && (
            <div className="absolute right-0 top-full mt-1.5 w-80 sm:w-96 rounded-lg border border-slate-200 bg-white p-2 shadow-xl z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 py-1">
                Search Results for "{searchQuery}"
              </div>

              {!hasSearchResults && (
                <div className="p-4 text-center text-xs text-slate-500">
                  No matching items, SKUs, or documents found.
                </div>
              )}

              {/* Products */}
              {searchProducts.length > 0 && (
                <div className="mb-2">
                  <div className="px-2 py-0.5 text-[11px] font-semibold text-sky-700 bg-sky-50 rounded-xs mb-1">
                    Products ({searchProducts.length})
                  </div>
                  {searchProducts.map((p) => {
                    const total = Object.values(p.warehouseStock || {}).reduce((a, b) => a + b, 0);
                    return (
                      <button
                        key={p.id}
                        onClick={() => {
                          setActiveView('products');
                          setIsSearchOpen(false);
                          setSearchQuery('');
                        }}
                        className="w-full flex items-center justify-between p-2 text-left hover:bg-slate-50 rounded-md transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Package className="h-4 w-4 text-slate-500" />
                          <div>
                            <div className="text-xs font-medium text-slate-900">{p.name}</div>
                            <div className="text-[10px] text-slate-500">
                              SKU: <span className="font-mono">{p.sku}</span> | {p.category}
                            </div>
                          </div>
                        </div>
                        <span className="text-xs font-semibold text-slate-700">
                          {total} {p.unit}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Receipts */}
              {searchReceipts.length > 0 && (
                <div className="mb-2">
                  <div className="px-2 py-0.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 rounded-xs mb-1">
                    Receipts ({searchReceipts.length})
                  </div>
                  {searchReceipts.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => {
                        setActiveView('receipts');
                        setIsSearchOpen(false);
                        setSearchQuery('');
                      }}
                      className="w-full flex items-center justify-between p-2 text-left hover:bg-slate-50 rounded-md transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-emerald-600" />
                        <div>
                          <div className="text-xs font-medium text-slate-900">{r.receiptNo}</div>
                          <div className="text-[10px] text-slate-500">Vendor: {r.supplier}</div>
                        </div>
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-xs bg-slate-100 text-slate-700">
                        {r.status}
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {/* Deliveries */}
              {searchDeliveries.length > 0 && (
                <div>
                  <div className="px-2 py-0.5 text-[11px] font-semibold text-blue-700 bg-blue-50 rounded-xs mb-1">
                    Deliveries ({searchDeliveries.length})
                  </div>
                  {searchDeliveries.map((d) => (
                    <button
                      key={d.id}
                      onClick={() => {
                        setActiveView('deliveries');
                        setIsSearchOpen(false);
                        setSearchQuery('');
                      }}
                      className="w-full flex items-center justify-between p-2 text-left hover:bg-slate-50 rounded-md transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-blue-600" />
                        <div>
                          <div className="text-xs font-medium text-slate-900">{d.deliveryNo}</div>
                          <div className="text-[10px] text-slate-500">Customer: {d.customer}</div>
                        </div>
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-xs bg-slate-100 text-slate-700">
                        {d.status}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Notifications Dropdown */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => setIsNotifOpen(!isNotifOpen)}
            className="relative rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
            title="Notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadNotifCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white ring-2 ring-white animate-pulse">
                {unreadNotifCount}
              </span>
            )}
          </button>

          {isNotifOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 rounded-lg border border-slate-200 bg-white shadow-xl z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="flex items-center justify-between border-b border-slate-200 p-3 bg-slate-50/50">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-900">Notifications</span>
                  {unreadNotifCount > 0 && (
                    <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-700">
                      {unreadNotifCount} unread
                    </span>
                  )}
                </div>
                {unreadNotifCount > 0 && (
                  <button
                    onClick={markAllNotificationsRead}
                    className="flex items-center gap-1 text-[11px] font-medium text-sky-700 hover:text-sky-900"
                  >
                    <CheckCheck className="h-3 w-3" />
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500">No notifications.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => {
                        markNotificationRead(n.id);
                        if (n.linkView) setActiveView(n.linkView);
                        setIsNotifOpen(false);
                      }}
                      className={`p-3 text-left transition-colors cursor-pointer hover:bg-slate-50 ${
                        !n.read ? 'bg-sky-50/40 font-medium' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span
                          className={`text-xs font-semibold ${
                            n.type === 'low_stock' ? 'text-rose-700' : 'text-slate-900'
                          }`}
                        >
                          {n.title}
                        </span>
                        <span className="text-[10px] text-slate-400 whitespace-nowrap">{n.timestamp}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-600 leading-snug">{n.message}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Dropdown */}
        <div ref={userMenuRef} className="relative">
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className="flex items-center gap-2 rounded-md p-1 text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <div className="h-7 w-7 rounded-full bg-sky-700 text-white flex items-center justify-center font-bold text-xs shadow-xs">
              VS
            </div>
            <div className="hidden md:block text-left">
              <div className="text-xs font-semibold text-slate-900 leading-tight">Vikramjit Singh</div>
              <div className="text-[10px] text-slate-500">Ops Lead</div>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {isUserMenuOpen && (
            <div className="absolute right-0 top-full mt-2 w-48 rounded-lg border border-slate-200 bg-white p-1 shadow-xl z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-2 border-b border-slate-100">
                <p className="text-xs font-semibold text-slate-900">{currentUser.name}</p>
                <p className="text-[10px] text-slate-500 truncate">{currentUser.email}</p>
              </div>
              <button
                onClick={() => {
                  setActiveView('profile');
                  setIsUserMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
              >
                <UserIcon className="h-3.5 w-3.5 text-slate-500" />
                Profile & Settings
              </button>
              <button
                onClick={() => {
                  setActiveView('warehouses');
                  setIsUserMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
              >
                <Warehouse className="h-3.5 w-3.5 text-slate-500" />
                Warehouse Setup
              </button>
              <div className="border-t border-slate-100 my-1" />
              <button
                onClick={() => {
                  setIsUserMenuOpen(false);
                  onLogoutClick();
                }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-rose-700 hover:bg-rose-50 rounded-md transition-colors"
              >
                <LogOut className="h-3.5 w-3.5 text-rose-600" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
