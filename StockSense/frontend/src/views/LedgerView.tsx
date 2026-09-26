import React, { useState } from 'react';
import { Download, Search, FilterX, History } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';

export const LedgerView: React.FC = () => {
  const { stockLedger, warehouses, products, showToast } = useInventory();

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [warehouseFilter, setWarehouseFilter] = useState('all');
  const [productFilter, setProductFilter] = useState('all');

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const filteredLedger = stockLedger.filter((entry) => {
    const matchesSearch =
      entry.referenceNo.toLowerCase().includes(search.toLowerCase()) ||
      entry.productName.toLowerCase().includes(search.toLowerCase()) ||
      entry.sku.toLowerCase().includes(search.toLowerCase()) ||
      entry.performedBy.toLowerCase().includes(search.toLowerCase());

    const matchesType = typeFilter === 'all' || entry.type === typeFilter;
    const matchesWarehouse = warehouseFilter === 'all' || entry.warehouseId === warehouseFilter;
    const matchesProduct = productFilter === 'all' || entry.productId === productFilter;

    return matchesSearch && matchesType && matchesWarehouse && matchesProduct;
  });

  const totalPages = Math.ceil(filteredLedger.length / pageSize) || 1;
  const paginatedLedger = filteredLedger.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleClearFilters = () => {
    setSearch('');
    setTypeFilter('all');
    setWarehouseFilter('all');
    setProductFilter('all');
    setCurrentPage(1);
  };

  const handleExportCsv = () => {
    if (filteredLedger.length === 0) return;
    const headers = [
      'Timestamp',
      'Reference No',
      'Type',
      'Product Name',
      'SKU',
      'Warehouse',
      'From Location',
      'To Location',
      'Quantity Delta',
      'Before Stock',
      'After Stock',
      'Performed By',
    ];

    const rows = filteredLedger.map((e) => [
      e.timestamp,
      e.referenceNo,
      e.type,
      `"${e.productName}"`,
      e.sku,
      `"${e.warehouseName}"`,
      `"${e.fromLocation}"`,
      `"${e.toLocation}"`,
      e.quantity,
      e.beforeStock,
      e.afterStock,
      `"${e.performedBy}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `StockSense_Ledger_Export_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast('success', 'CSV Exported', 'Stock ledger audit log exported to CSV.');
  };

  return (
    <div className="space-y-5 pb-12 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Stock Ledger / Move History Audit Log</h1>
          <p className="text-xs text-slate-500 mt-0.5">Immutable audit trail of all receipts, customer dispatches, transfers, and stock adjustments</p>
        </div>

        <button
          onClick={handleExportCsv}
          className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
        >
          <Download className="h-4 w-4 text-slate-500" />
          Export CSV Audit Log
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-2.5 flex-1 min-w-[240px]">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search reference #, product, or performed by..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full rounded-md border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-800 focus:border-sky-500 focus:bg-white focus:outline-none"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Movement Type: All</option>
            <option value="Receipt">Receipt (Incoming)</option>
            <option value="Delivery">Delivery (Outgoing)</option>
            <option value="Transfer">Transfer (Internal)</option>
            <option value="Adjustment">Adjustment (Audit)</option>
          </select>

          <select
            value={warehouseFilter}
            onChange={(e) => {
              setWarehouseFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Warehouse: All Locations</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>

          <select
            value={productFilter}
            onChange={(e) => {
              setProductFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Product SKU: All</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} - {p.name}
              </option>
            ))}
          </select>
        </div>

        {(search || typeFilter !== 'all' || warehouseFilter !== 'all' || productFilter !== 'all') && (
          <button
            onClick={handleClearFilters}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-rose-700 underline"
          >
            <FilterX className="h-3.5 w-3.5" />
            Clear Filters
          </button>
        )}
      </div>

      {/* Ledger Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
        {filteredLedger.length === 0 ? (
          <EmptyState
            title="No Movement Audit Entries Found"
            description="No movement transactions match your query criteria."
            onClearFilters={handleClearFilters}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Date & Time</th>
                  <th className="px-4 py-3">Reference #</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Product Name</th>
                  <th className="px-4 py-3">SKU</th>
                  <th className="px-4 py-3">Warehouse</th>
                  <th className="px-4 py-3">From</th>
                  <th className="px-4 py-3">To</th>
                  <th className="px-4 py-3 text-right">Qty Delta</th>
                  <th className="px-4 py-3 text-right">Before</th>
                  <th className="px-4 py-3 text-right">After</th>
                  <th className="px-4 py-3">Performed By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {paginatedLedger.map((entry) => (
                  <tr key={entry.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">{entry.timestamp}</td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-900">{entry.referenceNo}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={entry.type} size="sm" />
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-900">{entry.productName}</td>
                    <td className="px-4 py-3 font-mono text-slate-600">{entry.sku}</td>
                    <td className="px-4 py-3 font-medium text-slate-700">{entry.warehouseName}</td>
                    <td className="px-4 py-3 text-slate-500 max-w-[140px] truncate" title={entry.fromLocation}>
                      {entry.fromLocation}
                    </td>
                    <td className="px-4 py-3 text-slate-500 max-w-[140px] truncate" title={entry.toLocation}>
                      {entry.toLocation}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-bold ${
                        entry.quantity > 0 ? 'text-emerald-700' : 'text-rose-700'
                      }`}
                    >
                      {entry.quantity > 0 ? `+${entry.quantity}` : entry.quantity}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-500 font-mono">{entry.beforeStock}</td>
                    <td className="px-4 py-3 text-right font-bold text-slate-900 font-mono">{entry.afterStock}</td>
                    <td className="px-4 py-3 text-slate-600">{entry.performedBy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {filteredLedger.length > 0 && (
          <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3 bg-slate-50/50 text-xs">
            <span className="text-slate-500">
              Showing <span className="font-semibold text-slate-800">{(currentPage - 1) * pageSize + 1}</span> to{' '}
              <span className="font-semibold text-slate-800">
                {Math.min(currentPage * pageSize, filteredLedger.length)}
              </span>{' '}
              of <span className="font-semibold text-slate-800">{filteredLedger.length}</span> audit logs
            </span>

            <div className="flex items-center gap-1">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="px-2 font-semibold text-slate-800">
                Page {currentPage} of {totalPages}
              </span>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
