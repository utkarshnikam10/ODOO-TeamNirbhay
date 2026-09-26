import React from 'react';
import { AlertTriangle, ShoppingCart, ArrowRight } from 'lucide-react';
import { useInventory } from '../../context/InventoryContext';
import { StatusBadge } from '../common/StatusBadge';

export const LowStockTable: React.FC = () => {
  const { products, warehouses, setActiveView, quickReorderProduct, showToast } = useInventory();

  // Filter low stock and out of stock products
  const lowStockProducts = products.filter((p) => {
    const total = Object.values(p.warehouseStock || {}).reduce((a, b) => a + b, 0);
    return total <= p.minReorderLevel;
  });

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-amber-100 text-amber-700">
            <AlertTriangle className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Low Stock & Reorder Alerts</h3>
            <p className="text-xs text-slate-500">Products currently at or below minimum reorder threshold</p>
          </div>
        </div>
        <button
          onClick={() => setActiveView('products')}
          className="flex items-center gap-1 text-xs font-semibold text-sky-700 hover:text-sky-900"
        >
          View All Inventory
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>

      {lowStockProducts.length === 0 ? (
        <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-md border border-slate-200">
          All products are abundantly stocked above reorder thresholds.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-3 py-2.5">Product Name</th>
                <th className="px-3 py-2.5">SKU</th>
                <th className="px-3 py-2.5">Primary Location</th>
                <th className="px-3 py-2.5">Current Stock</th>
                <th className="px-3 py-2.5">Reorder Level</th>
                <th className="px-3 py-2.5">Smart Suggested Order</th>
                <th className="px-3 py-2.5">Status</th>
                <th className="px-3 py-2.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {lowStockProducts.map((prod) => {
                const totalStock = Object.values(prod.warehouseStock || {}).reduce((a, b) => a + b, 0);
                const status = totalStock === 0 ? 'Out of Stock' : 'Low Stock';
                
                // Find primary warehouse location
                let primaryWhId = 'wh-001';
                let lowestQty = Infinity;
                Object.entries(prod.warehouseStock || {}).forEach(([whId, qty]) => {
                  if (qty < lowestQty) {
                    lowestQty = qty;
                    primaryWhId = whId;
                  }
                });
                const whName = warehouses.find((w) => w.id === primaryWhId)?.name || 'Main Warehouse';
                const suggestedQty = Math.max(prod.minReorderLevel * 2, (prod.minReorderLevel - totalStock) + (prod.minReorderLevel * 2));

                return (
                  <tr key={prod.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-3 py-2.5 font-semibold text-slate-900">{prod.name}</td>
                    <td className="px-3 py-2.5 font-mono text-slate-600">{prod.sku}</td>
                    <td className="px-3 py-2.5 text-slate-600">{whName}</td>
                    <td className="px-3 py-2.5 font-bold text-slate-900">
                      {totalStock} <span className="font-normal text-slate-500">{prod.unit}</span>
                    </td>
                    <td className="px-3 py-2.5 text-slate-600">
                      {prod.minReorderLevel} {prod.unit}
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                          +{suggestedQty} {prod.unit}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <StatusBadge status={status} size="sm" />
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <button
                        onClick={() => {
                          quickReorderProduct(prod.id, suggestedQty, primaryWhId);
                          setActiveView('receipts');
                          showToast('success', 'Reorder Receipt Draft Generated', `Suggested order created for ${prod.name}.`);
                        }}
                        className="inline-flex items-center gap-1 rounded border border-sky-300 bg-sky-50 px-2.5 py-1 text-[11px] font-semibold text-sky-800 hover:bg-sky-100 transition-colors"
                        title="Create quick reorder draft receipt"
                      >
                        <ShoppingCart className="h-3 w-3" />
                        Quick Reorder
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
