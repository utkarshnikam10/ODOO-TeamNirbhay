import React, { useState } from 'react';
import { Plus, SlidersHorizontal, Search, FilterX } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { AdjustmentFormModal } from '../components/adjustments/AdjustmentFormModal';
import { EmptyState } from '../components/common/EmptyState';

export const AdjustmentsView: React.FC = () => {
  const { adjustments, warehouses, products } = useInventory();

  const [search, setSearch] = useState('');
  const [warehouseFilter, setWarehouseFilter] = useState('all');

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const filteredAdjustments = adjustments.filter((adj) => {
    const p = products.find((pr) => pr.id === adj.productId);
    const matchesSearch =
      adj.adjustmentNo.toLowerCase().includes(search.toLowerCase()) ||
      adj.reason.toLowerCase().includes(search.toLowerCase()) ||
      (p && p.name.toLowerCase().includes(search.toLowerCase())) ||
      (p && p.sku.toLowerCase().includes(search.toLowerCase()));

    const matchesWarehouse = warehouseFilter === 'all' || adj.warehouseId === warehouseFilter;

    return matchesSearch && matchesWarehouse;
  });

  const handleClearFilters = () => {
    setSearch('');
    setWarehouseFilter('all');
  };

  return (
    <div className="space-y-5 pb-12 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Inventory Adjustments</h1>
          <p className="text-xs text-slate-500 mt-0.5">Reconcile differences between physical audit counts and recorded system inventory</p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-purple-700 px-4 py-2 text-xs font-semibold text-white hover:bg-purple-800 transition-colors shadow-xs"
        >
          <Plus className="h-4 w-4" />
          New Adjustment
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search adjustment #, product SKU, or reason..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-800 focus:border-sky-500 focus:bg-white focus:outline-none"
            />
          </div>

          <select
            value={warehouseFilter}
            onChange={(e) => setWarehouseFilter(e.target.value)}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Warehouse Location: All</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>

        {(search || warehouseFilter !== 'all') && (
          <button
            onClick={handleClearFilters}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-rose-700 underline"
          >
            <FilterX className="h-3.5 w-3.5" />
            Clear Filters
          </button>
        )}
      </div>

      {/* Adjustments Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
        {filteredAdjustments.length === 0 ? (
          <EmptyState
            title="No Adjustments Found"
            description="Try changing your search filters or execute a physical inventory adjustment."
            onClearFilters={handleClearFilters}
            actionLabel="New Adjustment"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Adjustment ID</th>
                  <th className="px-4 py-3">Product Name & SKU</th>
                  <th className="px-4 py-3">Warehouse Location</th>
                  <th className="px-4 py-3 text-right">System Qty</th>
                  <th className="px-4 py-3 text-right">Physical Count</th>
                  <th className="px-4 py-3 text-right">Difference Variance</th>
                  <th className="px-4 py-3">Reason Code</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Auditor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {filteredAdjustments.map((adj) => {
                  const p = products.find((pr) => pr.id === adj.productId);
                  const wh = warehouses.find((w) => w.id === adj.warehouseId);

                  return (
                    <tr key={adj.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{adj.adjustmentNo}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900">{p?.name || 'Product'}</div>
                        <div className="text-[10px] font-mono text-slate-500">{p?.sku}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-700 font-medium">
                        {wh ? `${wh.name} (${wh.code})` : 'Warehouse'}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-slate-800">{adj.systemQuantity}</td>
                      <td className="px-4 py-3 text-right font-bold text-sky-900">{adj.physicalQuantity}</td>
                      <td className="px-4 py-3 text-right">
                        <span
                          className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                            adj.difference === 0
                              ? 'bg-slate-100 text-slate-700'
                              : adj.difference > 0
                              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                              : 'bg-rose-50 text-rose-800 border border-rose-200'
                          }`}
                        >
                          {adj.difference > 0 ? `+${adj.difference}` : adj.difference} {p?.unit}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600 max-w-xs truncate">{adj.reason}</td>
                      <td className="px-4 py-3 text-slate-500">{adj.date}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={adj.status} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-slate-500">{adj.createdBy}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <AdjustmentFormModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
    </div>
  );
};
