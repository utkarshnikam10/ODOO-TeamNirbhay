import React, { useState } from 'react';
import {
  Package,
  AlertTriangle,
  XCircle,
  ArrowDownLeft,
  ArrowUpRight,
  ArrowRightLeft,
  RefreshCw,
  FilterX,
  Warehouse as WarehouseIcon,
} from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { KpiCard } from '../components/common/KpiCard';
import { AnalyticsCharts } from '../components/dashboard/AnalyticsCharts';
import { LowStockTable } from '../components/dashboard/LowStockTable';
import { RecentActivityFeed } from '../components/dashboard/RecentActivityFeed';
import { ViewType } from '../types';

export const DashboardView: React.FC = () => {
  const {
    kpiStats,
    warehouses,
    selectedWarehouseFilter,
    setSelectedWarehouseFilter,
    setActiveView,
    resetToDefaultData,
    showToast,
  } = useInventory();

  const [documentTypeFilter, setDocumentTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      showToast('info', 'Dashboard Refreshed', 'Stock counts and metrics updated.');
    }, 400);
  };

  const handleClearFilters = () => {
    setDocumentTypeFilter('all');
    setStatusFilter('all');
    setSelectedWarehouseFilter('all');
    setCategoryFilter('all');
    showToast('info', 'Filters Reset', 'All dashboard filters cleared.');
  };

  const hasActiveFilters =
    documentTypeFilter !== 'all' ||
    statusFilter !== 'all' ||
    selectedWarehouseFilter !== 'all' ||
    categoryFilter !== 'all';

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* Top Header & Warehouse Selector */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Operations Dashboard</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time overview of warehouse stock levels, movement velocity, and open fulfillments
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Warehouse Selector */}
          <div className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 shadow-2xs">
            <WarehouseIcon className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={selectedWarehouseFilter}
              onChange={(e) => setSelectedWarehouseFilter(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-800 focus:outline-none"
            >
              <option value="all">All Warehouses (Company Total)</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.code})
                </option>
              ))}
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
            title="Refresh dashboard metrics"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-sky-600' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">Filter View:</span>

          <select
            value={documentTypeFilter}
            onChange={(e) => {
              setDocumentTypeFilter(e.target.value);
              if (e.target.value !== 'all') setActiveView(e.target.value as ViewType);
            }}
            className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-slate-800 focus:outline-none"
          >
            <option value="all">Document: All Types</option>
            <option value="receipts">Receipts</option>
            <option value="deliveries">Delivery Orders</option>
            <option value="transfers">Internal Transfers</option>
            <option value="adjustments">Adjustments</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-slate-800 focus:outline-none"
          >
            <option value="all">Status: All</option>
            <option value="Draft">Draft</option>
            <option value="Waiting">Waiting</option>
            <option value="Ready">Ready</option>
            <option value="Done">Done</option>
            <option value="Canceled">Canceled</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-slate-800 focus:outline-none"
          >
            <option value="all">Category: All</option>
            <option value="Raw Materials">Raw Materials</option>
            <option value="Finished Goods">Finished Goods</option>
            <option value="Packaging">Packaging</option>
            <option value="Electrical">Electrical</option>
            <option value="Tools">Tools</option>
            <option value="Safety Equipment">Safety Equipment</option>
          </select>
        </div>

        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="inline-flex items-center gap-1 rounded text-xs font-medium text-slate-600 hover:text-rose-700 underline"
          >
            <FilterX className="h-3.5 w-3.5" />
            Clear Filters
          </button>
        )}
      </div>

      {/* 6 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard
          title="Total Units in Stock"
          value={kpiStats.totalUnitsInStock}
          subtitle={`${kpiStats.totalProductsCount} SKUs`}
          icon={Package}
          variant="sky"
          onClick={() => setActiveView('products')}
        />

        <KpiCard
          title="Low Stock Items"
          value={kpiStats.lowStockCount}
          subtitle="Reorder alert"
          icon={AlertTriangle}
          variant="amber"
          onClick={() => setActiveView('products')}
        />

        <KpiCard
          title="Out of Stock"
          value={kpiStats.outOfStockCount}
          subtitle="Zero stock"
          icon={XCircle}
          variant="rose"
          onClick={() => setActiveView('products')}
        />

        <KpiCard
          title="Pending Receipts"
          value={kpiStats.pendingReceiptsCount}
          subtitle="Inbound vendor"
          icon={ArrowDownLeft}
          variant="emerald"
          onClick={() => setActiveView('receipts')}
        />

        <KpiCard
          title="Pending Deliveries"
          value={kpiStats.pendingDeliveriesCount}
          subtitle="Outbound customer"
          icon={ArrowUpRight}
          variant="sky"
          onClick={() => setActiveView('deliveries')}
        />

        <KpiCard
          title="Internal Transfers"
          value={kpiStats.internalTransfersCount}
          subtitle="Inter-warehouse"
          icon={ArrowRightLeft}
          variant="default"
          onClick={() => setActiveView('transfers')}
        />
      </div>

      {/* Operational Charts */}
      <AnalyticsCharts />

      {/* Low Stock Table & Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <LowStockTable />
        </div>
        <div>
          <RecentActivityFeed />
        </div>
      </div>
    </div>
  );
};
