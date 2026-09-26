import React, { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import { useInventory } from '../../context/InventoryContext';

interface ReceiptFormModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ReceiptFormModal: React.FC<ReceiptFormModalProps> = ({ isOpen, onClose }) => {
  const { createReceipt, products, warehouses, showToast } = useInventory();

  const [supplier, setSupplier] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [destinationWarehouseId, setDestinationWarehouseId] = useState('wh-001');
  const [items, setItems] = useState<{ productId: string; quantity: number; unitPrice?: number }[]>([
    { productId: products[0]?.id || '', quantity: 50, unitPrice: 100 },
  ]);
  const [notes, setNotes] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleAddItem = () => {
    setItems((prev) => [...prev, { productId: products[0]?.id || '', quantity: 10, unitPrice: 0 }]);
  };

  const handleRemoveItem = (index: number) => {
    if (items.length > 1) {
      setItems((prev) => prev.filter((_, i) => i !== index));
    }
  };

  const handleItemChange = (index: number, field: string, value: any) => {
    setItems((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!supplier.trim()) errs.supplier = 'Supplier Name is required.';
    if (!date) errs.date = 'Receipt Date is required.';
    if (items.length === 0) errs.items = 'At least one product line item is required.';

    items.forEach((it, idx) => {
      if (!it.productId) errs[`item_${idx}`] = 'Please select a product.';
      if (!it.quantity || it.quantity <= 0) errs[`qty_${idx}`] = 'Quantity must be > 0.';
    });

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    createReceipt({
      supplier: supplier.trim(),
      date,
      destinationWarehouseId,
      items,
      notes: notes.trim(),
    });

    onClose();
    // Reset form
    setSupplier('');
    setDate(new Date().toISOString().split('T')[0]);
    setDestinationWarehouseId('wh-001');
    setItems([{ productId: products[0]?.id || '', quantity: 50, unitPrice: 100 }]);
    setNotes('');
    setErrors({});
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Goods Receipt (Incoming)" maxWidth="2xl">
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Vendor / Supplier Name *</label>
            <input
              type="text"
              placeholder="e.g. Tata Steel Supplies"
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
            {errors.supplier && <p className="mt-1 text-[11px] text-rose-600">{errors.supplier}</p>}
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Receipt Date *</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Destination Warehouse</label>
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

        {/* Line Items Table */}
        <div className="border border-slate-200 rounded-md p-3 bg-slate-50/50 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-slate-800">Inbound Product Items</h4>
            <button
              type="button"
              onClick={handleAddItem}
              className="inline-flex items-center gap-1 text-xs font-semibold text-sky-700 hover:text-sky-900"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Product Line
            </button>
          </div>

          {items.map((item, idx) => (
            <div key={idx} className="flex flex-wrap items-center gap-2 bg-white p-2.5 rounded-md border border-slate-200 shadow-xs">
              <div className="flex-1 min-w-[200px]">
                <label className="text-[10px] text-slate-500 font-medium">Product Item</label>
                <select
                  value={item.productId}
                  onChange={(e) => handleItemChange(idx, 'productId', e.target.value)}
                  className="w-full rounded border border-slate-300 p-1.5 text-xs"
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku}) - Current Total: {Object.values(p.warehouseStock || {}).reduce((a, b) => a + b, 0)} {p.unit}
                    </option>
                  ))}
                </select>
              </div>

              <div className="w-28">
                <label className="text-[10px] text-slate-500 font-medium">Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={item.quantity}
                  onChange={(e) => handleItemChange(idx, 'quantity', Number(e.target.value))}
                  className="w-full rounded border border-slate-300 p-1.5 text-xs"
                />
              </div>

              <div className="w-28">
                <label className="text-[10px] text-slate-500 font-medium">Est. Unit Price (₹)</label>
                <input
                  type="number"
                  min="0"
                  value={item.unitPrice || 0}
                  onChange={(e) => handleItemChange(idx, 'unitPrice', Number(e.target.value))}
                  className="w-full rounded border border-slate-300 p-1.5 text-xs"
                />
              </div>

              <button
                type="button"
                onClick={() => handleRemoveItem(idx)}
                disabled={items.length === 1}
                className="mt-4 p-1 text-slate-400 hover:text-rose-600 disabled:opacity-40"
                title="Remove line item"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">Notes / PO Reference</label>
          <input
            type="text"
            placeholder="e.g. Purchase Order PO-8821, Gate Entry clearance"
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
            className="px-4 py-2 text-xs font-semibold text-white bg-sky-700 rounded-md hover:bg-sky-800 transition-colors shadow-xs"
          >
            Save Draft Receipt
          </button>
        </div>
      </form>
    </Modal>
  );
};
