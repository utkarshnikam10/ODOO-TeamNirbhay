import React, { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import { useInventory } from '../../context/InventoryContext';
import { Product } from '../../types';

interface TransferFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedProduct?: Product | null;
}

export const TransferFormModal: React.FC<TransferFormModalProps> = ({
  isOpen,
  onClose,
  preselectedProduct,
}) => {
  const { createTransfer, products, warehouses } = useInventory();

  const [sourceWarehouseId, setSourceWarehouseId] = useState('wh-001');
  const [destinationWarehouseId, setDestinationWarehouseId] = useState('wh-002');
  const [productId, setProductId] = useState(preselectedProduct?.id || products[0]?.id || '');
  const [quantity, setQuantity] = useState(10);
  const [reason, setReason] = useState('Production floor supply replenishment');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (preselectedProduct) {
      setProductId(preselectedProduct.id);
    }
  }, [preselectedProduct]);

  const selectedProd = products.find((p) => p.id === productId);
  const availInSource = selectedProd ? selectedProd.warehouseStock[sourceWarehouseId] || 0 : 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (sourceWarehouseId === destinationWarehouseId) {
      setErrorMessage('Source and Destination warehouses cannot be the same location.');
      return;
    }

    if (quantity <= 0) {
      setErrorMessage('Transfer quantity must be greater than 0.');
      return;
    }

    if (quantity > availInSource) {
      setErrorMessage(
        `Quantity (${quantity} ${selectedProd?.unit}) exceeds available stock (${availInSource} ${selectedProd?.unit}) in source warehouse.`
      );
      return;
    }

    const res = createTransfer({
      sourceWarehouseId,
      destinationWarehouseId,
      items: [{ productId, quantity }],
      reason: reason.trim(),
      date,
    });

    if (!res.success) {
      setErrorMessage(res.message || 'Error creating transfer.');
      return;
    }

    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Internal Stock Transfer" maxWidth="lg">
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        {errorMessage && (
          <div className="flex items-start gap-2 p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>{errorMessage}</div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">From (Source Warehouse) *</label>
            <select
              value={sourceWarehouseId}
              onChange={(e) => setSourceWarehouseId(e.target.value)}
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
            <label className="block font-medium text-slate-700 mb-1">To (Destination Warehouse) *</label>
            <select
              value={destinationWarehouseId}
              onChange={(e) => setDestinationWarehouseId(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            >
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.code})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">Product Item *</label>
          <select
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none font-semibold text-slate-800"
          >
            {products.map((p) => {
              const srcStock = p.warehouseStock[sourceWarehouseId] || 0;
              return (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku}) — Available in Source: {srcStock} {p.unit}
                </option>
              );
            })}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <div className="flex justify-between items-center mb-1 font-medium text-slate-700">
              <span>Transfer Quantity *</span>
              <span className="text-[10px] text-slate-500">Avail: {availInSource} {selectedProd?.unit}</span>
            </div>
            <input
              type="number"
              min="1"
              max={availInSource}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Transfer Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">Reason / Operational Purpose *</label>
          <input
            type="text"
            placeholder="e.g. Production floor assembly line demand"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
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
            className="px-4 py-2 text-xs font-semibold text-white bg-amber-600 rounded-md hover:bg-amber-700 transition-colors shadow-xs"
          >
            Create Transfer Record
          </button>
        </div>
      </form>
    </Modal>
  );
};
