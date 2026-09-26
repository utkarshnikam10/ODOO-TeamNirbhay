import React, { useState } from 'react';
import { Plus, Warehouse as WarehouseIcon, MapPin, Package, AlertTriangle, Edit2, ToggleLeft, ToggleRight } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { WarehouseFormModal } from '../components/warehouses/WarehouseFormModal';

export const WarehousesView: React.FC = () => {
  const { warehouses, products, toggleWarehouseStatus } = useInventory();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  return (
    <div className="space-y-5 pb-12 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Warehouse Facilities Management</h1>
          <p className="text-xs text-slate-500 mt-0.5">Configure storage locations, distribution hubs, and physical plant capacity</p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-sky-700 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-800 transition-colors shadow-xs"
        >
          <Plus className="h-4 w-4" />
          Add Warehouse
        </button>
      </div>

      {/* Warehouse Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {warehouses.map((wh) => {
          // Calculate warehouse metrics
          let totalProductsInWh = 0;
          let totalUnitsInWh = 0;
          let lowStockInWh = 0;

          products.forEach((p) => {
            const qty = p.warehouseStock[wh.id] || 0;
            if (qty > 0) totalProductsInWh++;
            totalUnitsInWh += qty;
            if (qty > 0 && qty <= Math.ceil(p.minReorderLevel / 2)) {
              lowStockInWh++;
            }
          });

          return (
            <div
              key={wh.id}
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow"
            >
              <div>
                <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-sky-800">
                      <WarehouseIcon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">{wh.name}</h3>
                      <span className="font-mono text-[11px] font-semibold text-slate-500">{wh.code}</span>
                    </div>
                  </div>
                  <StatusBadge status={wh.status} size="sm" />
                </div>

                <div className="mt-3 space-y-2 text-xs">
                  <div className="flex items-start gap-1.5 text-slate-600">
                    <MapPin className="h-3.5 w-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
                    <span>{wh.address}</span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-center">
                    <div className="p-2 bg-slate-50 rounded">
                      <span className="text-[10px] text-slate-400 font-semibold uppercase block">Products</span>
                      <span className="text-sm font-bold text-slate-900">{totalProductsInWh}</span>
                    </div>
                    <div className="p-2 bg-slate-50 rounded">
                      <span className="text-[10px] text-slate-400 font-semibold uppercase block">Total Units</span>
                      <span className="text-sm font-bold text-sky-800">{totalUnitsInWh.toLocaleString()}</span>
                    </div>
                    <div className="p-2 bg-slate-50 rounded">
                      <span className="text-[10px] text-slate-400 font-semibold uppercase block">Low Items</span>
                      <span className="text-sm font-bold text-amber-700">{lowStockInWh}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                <button
                  onClick={() => toggleWarehouseStatus(wh.id)}
                  className={`flex items-center gap-1 font-semibold ${
                    wh.status === 'Active' ? 'text-rose-600 hover:text-rose-800' : 'text-emerald-600 hover:text-emerald-800'
                  }`}
                >
                  {wh.status === 'Active' ? (
                    <>
                      <ToggleRight className="h-4 w-4" /> Deactivate
                    </>
                  ) : (
                    <>
                      <ToggleLeft className="h-4 w-4" /> Activate
                    </>
                  )}
                </button>

                <button
                  onClick={() => alert(`Edit warehouse details for ${wh.name}`)}
                  className="flex items-center gap-1 font-medium text-slate-600 hover:text-slate-900"
                >
                  <Edit2 className="h-3.5 w-3.5" /> Edit Details
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <WarehouseFormModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
    </div>
  );
};
