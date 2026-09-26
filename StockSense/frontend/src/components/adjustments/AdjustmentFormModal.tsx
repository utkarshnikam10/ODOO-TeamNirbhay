import React, { useState, useEffect } from 'react';
import { AlertCircle, Calculator } from 'lucide-react';
import { Modal } from '../common/Modal';
import { useInventory } from '../../context/InventoryContext';
import { Product } from '../../types';

interface AdjustmentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedProduct?: Product | null;
}

export const AdjustmentFormModal: React.FC<AdjustmentFormModalProps> = ({
  isOpen,
  onClose,
  preselectedProduct,
}) => {
  const { createAdjustment, products, warehouses } = useInventory();

  const [warehouseId, setWarehouseId] = useState('wh-001');
  const [productId, setProductId] = useState(preselectedProduct?.id || products[0]?.id || '');
  const [physicalQuantity, setPhysicalQuantity] = useState<number>(0);
  const [reason, setReason] = useState('Quarterly audit physical count discrepancy');
  const [notes, setNotes] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (preselectedProduct) {
      setProductId(preselectedProduct.id);
      const sysQty = preselectedProduct.warehouseStock[warehouseId] || 0;
      setPhysicalQuantity(sysQty);
    }
  }, [preselectedProduct, warehouseId]);

  const selectedProd = products.find((p) => p.id === productId);
  const systemQty = selectedProd ? selectedProd.warehouseStock[warehouseId] || 0 : 0;

  // Auto-calculate variance difference
  const difference = physicalQuantity - systemQty;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (physicalQuantity < 0) {
      setErrorMessage('Physical count cannot be negative.');
      return;
    }

    if (!reason.trim()) {
      setErrorMessage('Please provide a reason code for this inventory adjustment.');
      return;
    }

    const res = createAdjustment({
      warehouseId,
      productId,
      physicalQuantity,
      reason: reason.trim(),
      notes: notes.trim(),
    });

    if (!res.success) {
      setErrorMessage(res.message);
      return;
    }

    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Execute Stock Audit Adjustment" maxWidth="lg">
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        {errorMessage && (
          <div className="flex items-start gap-2 p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>{errorMessage}</div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Target Warehouse Location *</label>
            <select
              value={warehouseId}
              onChange={(e) => {
                setWarehouseId(e.target.value);
                const p = products.find((pr) => pr.id === productId);
                if (p) setPhysicalQuantity(p.warehouseStock[e.target.value] || 0);
              }}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            >
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Product SKU *</label>
            <select
              value={productId}
              onChange={(e) => {
                setProductId(e.target.value);
                const p = products.find((pr) => pr.id === e.target.value);
                if (p) setPhysicalQuantity(p.warehouseStock[warehouseId] || 0);
              }}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none font-semibold text-slate-800"
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Auto Calculation Card */}
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3.5 space-y-3">
          <div className="flex items-center gap-1.5 font-bold text-slate-900 border-b border-slate-200 pb-2">
            <Calculator className="h-4 w-4 text-purple-600" />
            Stock Variance Calculator
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-2 bg-white rounded border border-slate-200">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold block">System Record Qty</span>
              <span className="text-base font-bold text-slate-900">
                {systemQty} <span className="text-xs font-normal text-slate-500">{selectedProd?.unit}</span>
              </span>
            </div>

            <div className="p-2 bg-white rounded border border-sky-300 shadow-2xs">
              <span className="text-[10px] uppercase tracking-wider text-sky-700 font-semibold block">Physical Count Qty</span>
              <input
                type="number"
                min="0"
                value={physicalQuantity}
                onChange={(e) => setPhysicalQuantity(Number(e.target.value))}
                className="w-full text-center text-base font-bold text-sky-900 focus:outline-none bg-transparent"
              />
            </div>

            <div
              className={`p-2 rounded border ${
                difference === 0
                  ? 'bg-slate-100 border-slate-200 text-slate-700'
                  : difference > 0
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : 'bg-rose-50 border-rose-200 text-rose-900'
              }`}
            >
              <span className="text-[10px] uppercase tracking-wider font-semibold block">Calculated Variance</span>
              <span className="text-base font-bold">
                {difference > 0 ? `+${difference}` : difference}{' '}
                <span className="text-xs font-normal">{selectedProd?.unit}</span>
              </span>
            </div>
          </div>
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">Audit Discrepancy Reason *</label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
          >
            <option value="Quarterly audit physical count discrepancy">Quarterly audit physical count discrepancy</option>
            <option value="Damaged material discard / scrapped">Damaged material discard / scrapped</option>
            <option value="Material rusting / quality deterioration">Material rusting / quality deterioration</option>
            <option value="Cutting & sizing fabrication loss">Cutting & sizing fabrication loss</option>
            <option value="Found unrecorded stock stack">Found unrecorded stock stack</option>
            <option value="Expired shelf-life disposal">Expired shelf-life disposal</option>
            <option value="Testing & quality bench consumption">Testing & quality bench consumption</option>
          </select>
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">Auditor Notes</label>
          <textarea
            rows={2}
            placeholder="Audit log references, supervisor signatures..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
          />
        </div>

        <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 text-xs font-semibold text-white bg-purple-700 rounded-md hover:bg-purple-800 transition-colors shadow-xs"
          >
            Confirm & Apply Adjustment
          </button>
        </div>
      </form>
    </Modal>
  );
};
