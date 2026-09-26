import React from 'react';
import { Package, Warehouse as WarehouseIcon, History, ArrowRightLeft, SlidersHorizontal, Edit3 } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Product } from '../../types';
import { useInventory } from '../../context/InventoryContext';
import { StatusBadge } from '../common/StatusBadge';

interface ProductDetailModalProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenTransfer: (product: Product) => void;
  onOpenAdjustment: (product: Product) => void;
}

export const ProductDetailModal: React.FC<ProductDetailModalProps> = ({
  product,
  isOpen,
  onClose,
  onOpenTransfer,
  onOpenAdjustment,
}) => {
  const { warehouses, stockLedger } = useInventory();

  if (!product) return null;

  const totalStock = Object.values(product.warehouseStock || {}).reduce((a, b) => a + b, 0);
  const stockStatus =
    totalStock === 0 ? 'Out of Stock' : totalStock <= product.minReorderLevel ? 'Low Stock' : 'In Stock';

  // Filter recent movement history for this specific SKU
  const productMovements = stockLedger
    .filter((entry) => entry.productId === product.id || entry.sku === product.sku)
    .slice(0, 6);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Product Specification: ${product.name}`} maxWidth="xl">
      <div className="space-y-5 text-xs text-slate-700">
        {/* Top Header Card */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-sky-700 text-white shadow-xs">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">{product.name}</h3>
                <StatusBadge status={stockStatus} size="sm" />
              </div>
              <p className="text-xs text-slate-500">
                SKU: <span className="font-mono font-bold text-slate-700">{product.sku}</span> | Category:{' '}
                <span className="font-medium text-slate-700">{product.category}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-right">
            <div>
              <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold block">Total Available Stock</span>
              <span className="text-xl font-bold text-slate-900">
                {totalStock.toLocaleString()} <span className="text-xs font-normal text-slate-500">{product.unit}</span>
              </span>
            </div>
            <div className="border-l border-slate-200 pl-4">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold block">Reorder Level</span>
              <span className="text-sm font-semibold text-slate-700">
                {product.minReorderLevel} {product.unit}
              </span>
            </div>
          </div>
        </div>

        {/* Description */}
        {product.description && (
          <div className="text-xs text-slate-600 bg-white p-3 rounded-md border border-slate-200">
            <span className="font-semibold text-slate-800">Description: </span>
            {product.description}
          </div>
        )}

        {/* Warehouse-wise Breakdown */}
        <div>
          <h4 className="font-bold text-slate-900 mb-2 flex items-center gap-1.5">
            <WarehouseIcon className="h-4 w-4 text-sky-700" />
            Warehouse Location Breakdown
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {warehouses.map((wh) => {
              const qty = product.warehouseStock[wh.id] || 0;
              const pct = totalStock > 0 ? Math.round((qty / totalStock) * 100) : 0;
              return (
                <div key={wh.id} className="rounded-md border border-slate-200 bg-white p-3">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-800">
                    <span>{wh.name}</span>
                    <span className="text-[10px] font-mono text-slate-500">{wh.code}</span>
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="text-base font-bold text-slate-900">
                      {qty.toLocaleString()} <span className="text-xs font-normal text-slate-500">{product.unit}</span>
                    </span>
                    <span className="text-[11px] font-medium text-slate-500">{pct}% of total</span>
                  </div>
                  <div className="mt-1.5 h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full bg-sky-600 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Movement History Table */}
        <div>
          <h4 className="font-bold text-slate-900 mb-2 flex items-center gap-1.5">
            <History className="h-4 w-4 text-slate-600" />
            Recent Stock Movements for {product.sku}
          </h4>
          {productMovements.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500 bg-slate-50 rounded-md border border-slate-200">
              No recent movements logged for this item yet.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-[10px] uppercase font-bold text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="p-2">Date</th>
                    <th className="p-2">Reference</th>
                    <th className="p-2">Type</th>
                    <th className="p-2">Warehouse</th>
                    <th className="p-2 text-right">Qty</th>
                    <th className="p-2 text-right">After Stock</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {productMovements.map((mov) => (
                    <tr key={mov.id} className="hover:bg-slate-50">
                      <td className="p-2 text-slate-500">{mov.timestamp.split(' ')[0]}</td>
                      <td className="p-2 font-mono font-semibold text-slate-900">{mov.referenceNo}</td>
                      <td className="p-2">
                        <StatusBadge status={mov.type} size="sm" />
                      </td>
                      <td className="p-2 text-slate-600">{mov.warehouseName}</td>
                      <td className={`p-2 text-right font-bold ${mov.quantity > 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                        {mov.quantity > 0 ? `+${mov.quantity}` : mov.quantity}
                      </td>
                      <td className="p-2 text-right font-semibold text-slate-900">{mov.afterStock}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                onClose();
                onOpenTransfer(product);
              }}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <ArrowRightLeft className="h-3.5 w-3.5 text-amber-600" />
              Transfer Stock
            </button>
            <button
              type="button"
              onClick={() => {
                onClose();
                onOpenAdjustment(product);
              }}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <SlidersHorizontal className="h-3.5 w-3.5 text-purple-600" />
              Adjust Stock
            </button>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-white bg-slate-800 rounded-md hover:bg-slate-900 transition-colors"
          >
            Done / Close
          </button>
        </div>
      </div>
    </Modal>
  );
};
