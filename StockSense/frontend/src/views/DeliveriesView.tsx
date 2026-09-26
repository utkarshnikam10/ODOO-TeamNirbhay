import React, { useState } from 'react';
import { Plus, CheckCircle2, XCircle, Search, FilterX } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { DeliveryOrder } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { DeliveryFormModal } from '../components/deliveries/DeliveryFormModal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { EmptyState } from '../components/common/EmptyState';

export const DeliveriesView: React.FC = () => {
  const { deliveries, validateDelivery, cancelDelivery, warehouses, products } = useInventory();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [warehouseFilter, setWarehouseFilter] = useState('all');

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [confirmDelivery, setConfirmDelivery] = useState<DeliveryOrder | null>(null);

  const filteredDeliveries = deliveries.filter((del) => {
    const matchesSearch =
      del.deliveryNo.toLowerCase().includes(search.toLowerCase()) ||
      del.customer.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'all' || del.status === statusFilter;
    const matchesWarehouse = warehouseFilter === 'all' || del.sourceWarehouseId === warehouseFilter;

    return matchesSearch && matchesStatus && matchesWarehouse;
  });

  const handleClearFilters = () => {
    setSearch('');
    setStatusFilter('all');
    setWarehouseFilter('all');
  };

  return (
    <div className="space-y-5 pb-12 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Delivery Orders (Outgoing)</h1>
          <p className="text-xs text-slate-500 mt-0.5">Track outgoing shipments to customers and process warehouse stock dispatches</p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-blue-700 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-800 transition-colors shadow-xs"
        >
          <Plus className="h-4 w-4" />
          New Delivery Order
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search delivery # or customer..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-800 focus:border-sky-500 focus:bg-white focus:outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Status: All</option>
            <option value="Draft">Draft</option>
            <option value="Waiting">Waiting</option>
            <option value="Ready">Ready</option>
            <option value="Done">Done (Dispatched)</option>
            <option value="Canceled">Canceled</option>
          </select>

          <select
            value={warehouseFilter}
            onChange={(e) => setWarehouseFilter(e.target.value)}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Source Warehouse: All</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>

        {(search || statusFilter !== 'all' || warehouseFilter !== 'all') && (
          <button
            onClick={handleClearFilters}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-rose-700 underline"
          >
            <FilterX className="h-3.5 w-3.5" />
            Clear Filters
          </button>
        )}
      </div>

      {/* Deliveries Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
        {filteredDeliveries.length === 0 ? (
          <EmptyState
            title="No Delivery Orders Found"
            description="Try changing your search filters or create a new outgoing customer delivery."
            onClearFilters={handleClearFilters}
            actionLabel="New Delivery Order"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Delivery ID</th>
                  <th className="px-4 py-3">Customer</th>
                  <th className="px-4 py-3">Dispatch Date</th>
                  <th className="px-4 py-3">Source WH</th>
                  <th className="px-4 py-3">Dispatched Items</th>
                  <th className="px-4 py-3 text-right">Total Units</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created By</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {filteredDeliveries.map((del) => {
                  const sourceWh = warehouses.find((w) => w.id === del.sourceWarehouseId);
                  const totalUnits = del.items.reduce((a, b) => a + b.quantity, 0);

                  return (
                    <tr key={del.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{del.deliveryNo}</td>
                      <td className="px-4 py-3 font-semibold text-slate-800">{del.customer}</td>
                      <td className="px-4 py-3 text-slate-600">{del.date}</td>
                      <td className="px-4 py-3 text-slate-600 font-medium">
                        {sourceWh ? `${sourceWh.name} (${sourceWh.code})` : 'Warehouse'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-0.5">
                          {del.items.map((it, idx) => {
                            const p = products.find((pr) => pr.id === it.productId);
                            return (
                              <div key={idx} className="text-slate-700">
                                • <span className="font-semibold">{p?.name || 'Item'}</span> (
                                <span className="font-bold text-rose-700">-{it.quantity}</span> {p?.unit})
                              </div>
                            );
                          })}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-slate-900">{totalUnits.toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={del.status} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-slate-500">{del.createdBy}</td>
                      <td className="px-4 py-3 text-right space-x-1">
                        {del.status !== 'Done' && del.status !== 'Canceled' && (
                          <>
                            <button
                              onClick={() => setConfirmDelivery(del)}
                              className="inline-flex items-center gap-1 rounded border border-blue-300 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-800 hover:bg-blue-100 transition-colors"
                            >
                              <CheckCircle2 className="h-3 w-3" />
                              Validate Dispatch
                            </button>
                            <button
                              onClick={() => cancelDelivery(del.id)}
                              className="p-1 rounded text-rose-600 hover:bg-rose-50"
                              title="Cancel order"
                            >
                              <XCircle className="h-4 w-4" />
                            </button>
                          </>
                        )}
                        {del.status === 'Done' && (
                          <span className="text-[11px] font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                            Dispatched & Deducted
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <DeliveryFormModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />

      {/* Confirmation Dialog for Delivery Order Validation */}
      {confirmDelivery && (
        <ConfirmDialog
          isOpen={!!confirmDelivery}
          onClose={() => setConfirmDelivery(null)}
          onConfirm={() => validateDelivery(confirmDelivery.id)}
          title={`Validate Delivery Order ${confirmDelivery.deliveryNo}?`}
          message={`Validate and dispatch this delivery? ${confirmDelivery.items.reduce(
            (a, b) => a + b.quantity,
            0
          )} units will be removed from ${
            warehouses.find((w) => w.id === confirmDelivery.sourceWarehouseId)?.name || 'source warehouse'
          }.`}
          details={`Customer: ${confirmDelivery.customer} | Order: ${confirmDelivery.deliveryNo}`}
          confirmLabel="Confirm & Dispatch Stock"
          variant="primary"
        />
      )}
    </div>
  );
};
