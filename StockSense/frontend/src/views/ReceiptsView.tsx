import React, { useState } from 'react';
import { Plus, CheckCircle2, XCircle, FileText, Search, FilterX } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { Receipt } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ReceiptFormModal } from '../components/receipts/ReceiptFormModal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { EmptyState } from '../components/common/EmptyState';

export const ReceiptsView: React.FC = () => {
  const { receipts, validateReceipt, cancelReceipt, warehouses, products } = useInventory();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [warehouseFilter, setWarehouseFilter] = useState('all');

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [confirmReceipt, setConfirmReceipt] = useState<Receipt | null>(null);

  const filteredReceipts = receipts.filter((rec) => {
    const matchesSearch =
      rec.receiptNo.toLowerCase().includes(search.toLowerCase()) ||
      rec.supplier.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'all' || rec.status === statusFilter;
    const matchesWarehouse =
      warehouseFilter === 'all' || rec.destinationWarehouseId === warehouseFilter;

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
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Goods Receipts (Incoming)</h1>
          <p className="text-xs text-slate-500 mt-0.5">Track incoming shipments and validate stock additions from vendors</p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-emerald-700 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors shadow-xs"
        >
          <Plus className="h-4 w-4" />
          New Receipt
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search receipt # or supplier..."
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
            <option value="Done">Done (Validated)</option>
            <option value="Canceled">Canceled</option>
          </select>

          <select
            value={warehouseFilter}
            onChange={(e) => setWarehouseFilter(e.target.value)}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Destination Warehouse: All</option>
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

      {/* Receipts Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
        {filteredReceipts.length === 0 ? (
          <EmptyState
            title="No Receipts Found"
            description="Try changing your filters or create a new inbound vendor receipt."
            onClearFilters={handleClearFilters}
            actionLabel="New Receipt"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Receipt ID</th>
                  <th className="px-4 py-3">Supplier</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Destination WH</th>
                  <th className="px-4 py-3">Products & Quantities</th>
                  <th className="px-4 py-3 text-right">Total Units</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created By</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {filteredReceipts.map((rec) => {
                  const targetWh = warehouses.find((w) => w.id === rec.destinationWarehouseId);
                  const totalUnits = rec.items.reduce((a, b) => a + b.quantity, 0);

                  return (
                    <tr key={rec.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{rec.receiptNo}</td>
                      <td className="px-4 py-3 font-semibold text-slate-800">{rec.supplier}</td>
                      <td className="px-4 py-3 text-slate-600">{rec.date}</td>
                      <td className="px-4 py-3 text-slate-600 font-medium">
                        {targetWh ? `${targetWh.name} (${targetWh.code})` : 'Warehouse'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-0.5">
                          {rec.items.map((it, idx) => {
                            const p = products.find((pr) => pr.id === it.productId);
                            return (
                              <div key={idx} className="text-slate-700">
                                • <span className="font-semibold">{p?.name || 'Item'}</span> (
                                <span className="font-bold text-emerald-700">+{it.quantity}</span> {p?.unit})
                              </div>
                            );
                          })}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-slate-900">{totalUnits.toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={rec.status} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-slate-500">{rec.createdBy}</td>
                      <td className="px-4 py-3 text-right space-x-1">
                        {rec.status !== 'Done' && rec.status !== 'Canceled' && (
                          <>
                            <button
                              onClick={() => setConfirmReceipt(rec)}
                              className="inline-flex items-center gap-1 rounded border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-800 hover:bg-emerald-100 transition-colors"
                            >
                              <CheckCircle2 className="h-3 w-3" />
                              Validate
                            </button>
                            <button
                              onClick={() => cancelReceipt(rec.id)}
                              className="p-1 rounded text-rose-600 hover:bg-rose-50"
                              title="Cancel receipt"
                            >
                              <XCircle className="h-4 w-4" />
                            </button>
                          </>
                        )}
                        {rec.status === 'Done' && (
                          <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                            Validated & Added
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

      <ReceiptFormModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />

      {/* Confirmation Dialog for Receipt Validation */}
      {confirmReceipt && (
        <ConfirmDialog
          isOpen={!!confirmReceipt}
          onClose={() => setConfirmReceipt(null)}
          onConfirm={() => validateReceipt(confirmReceipt.id)}
          title={`Validate Receipt ${confirmReceipt.receiptNo}?`}
          message={`Validate this receipt? ${confirmReceipt.items.reduce(
            (a, b) => a + b.quantity,
            0
          )} units will be automatically added to ${
            warehouses.find((w) => w.id === confirmReceipt.destinationWarehouseId)?.name || 'target warehouse'
          }.`}
          details={`Vendor: ${confirmReceipt.supplier} | Reference: ${confirmReceipt.receiptNo}`}
          confirmLabel="Confirm & Add Stock"
          variant="primary"
        />
      )}
    </div>
  );
};
