import React, { useState } from 'react';
import { Plus, CheckCircle2, XCircle, Search, FilterX, ArrowRightLeft } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { InternalTransfer } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { TransferFormModal } from '../components/transfers/TransferFormModal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { EmptyState } from '../components/common/EmptyState';

export const TransfersView: React.FC = () => {
  const { transfers, validateTransfer, cancelTransfer, warehouses, products } = useInventory();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [confirmTransfer, setConfirmTransfer] = useState<InternalTransfer | null>(null);

  const filteredTransfers = transfers.filter((tr) => {
    const matchesSearch =
      tr.transferNo.toLowerCase().includes(search.toLowerCase()) ||
      tr.reason.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'all' || tr.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const handleClearFilters = () => {
    setSearch('');
    setStatusFilter('all');
  };

  return (
    <div className="space-y-5 pb-12 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Internal Stock Transfers</h1>
          <p className="text-xs text-slate-500 mt-0.5">Move inventory seamlessly between company warehouses and production bays</p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-amber-600 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-700 transition-colors shadow-xs"
        >
          <Plus className="h-4 w-4" />
          New Transfer
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search transfer # or reason..."
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
            <option value="Ready">Ready</option>
            <option value="Done">Done (Completed)</option>
            <option value="Canceled">Canceled</option>
          </select>
        </div>

        {(search || statusFilter !== 'all') && (
          <button
            onClick={handleClearFilters}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-rose-700 underline"
          >
            <FilterX className="h-3.5 w-3.5" />
            Clear Filters
          </button>
        )}
      </div>

      {/* Transfers Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
        {filteredTransfers.length === 0 ? (
          <EmptyState
            title="No Internal Transfers Found"
            description="Try changing your search filters or record a new warehouse transfer."
            onClearFilters={handleClearFilters}
            actionLabel="New Transfer"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Transfer ID</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Source (From)</th>
                  <th className="px-4 py-3">Destination (To)</th>
                  <th className="px-4 py-3">Product & Quantity</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created By</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {filteredTransfers.map((tr) => {
                  const srcWh = warehouses.find((w) => w.id === tr.sourceWarehouseId);
                  const destWh = warehouses.find((w) => w.id === tr.destinationWarehouseId);

                  return (
                    <tr key={tr.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{tr.transferNo}</td>
                      <td className="px-4 py-3 text-slate-600">{tr.date}</td>
                      <td className="px-4 py-3 font-semibold text-slate-800">
                        {srcWh ? `${srcWh.name} (${srcWh.code})` : 'Source'}
                      </td>
                      <td className="px-4 py-3 font-semibold text-sky-900">
                        {destWh ? `${destWh.name} (${destWh.code})` : 'Destination'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-0.5">
                          {tr.items.map((it, idx) => {
                            const p = products.find((pr) => pr.id === it.productId);
                            return (
                              <div key={idx} className="text-slate-800">
                                • <span className="font-semibold">{p?.name || 'Item'}</span> (
                                <span className="font-bold text-amber-700">{it.quantity}</span> {p?.unit})
                              </div>
                            );
                          })}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600 max-w-xs truncate">{tr.reason}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={tr.status} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-slate-500">{tr.createdBy}</td>
                      <td className="px-4 py-3 text-right space-x-1">
                        {tr.status !== 'Done' && tr.status !== 'Canceled' && (
                          <>
                            <button
                              onClick={() => setConfirmTransfer(tr)}
                              className="inline-flex items-center gap-1 rounded border border-amber-300 bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-800 hover:bg-amber-100 transition-colors"
                            >
                              <CheckCircle2 className="h-3 w-3" />
                              Execute Transfer
                            </button>
                            <button
                              onClick={() => cancelTransfer(tr.id)}
                              className="p-1 rounded text-rose-600 hover:bg-rose-50"
                              title="Cancel transfer"
                            >
                              <XCircle className="h-4 w-4" />
                            </button>
                          </>
                        )}
                        {tr.status === 'Done' && (
                          <span className="text-[11px] font-medium text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            Transfer Completed
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

      <TransferFormModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />

      {confirmTransfer && (
        <ConfirmDialog
          isOpen={!!confirmTransfer}
          onClose={() => setConfirmTransfer(null)}
          onConfirm={() => validateTransfer(confirmTransfer.id)}
          title={`Execute Internal Transfer ${confirmTransfer.transferNo}?`}
          message={`Execute transfer? Stock will be deducted from ${
            warehouses.find((w) => w.id === confirmTransfer.sourceWarehouseId)?.name
          } and added to ${
            warehouses.find((w) => w.id === confirmTransfer.destinationWarehouseId)?.name
          }. Total company stock remains unchanged.`}
          details={`Transfer ID: ${confirmTransfer.transferNo} | Reason: ${confirmTransfer.reason}`}
          confirmLabel="Confirm & Transfer Stock"
          variant="primary"
        />
      )}
    </div>
  );
};
