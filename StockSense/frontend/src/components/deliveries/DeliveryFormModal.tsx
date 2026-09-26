import React, { useState } from 'react';
import { Plus, Trash2, AlertCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import { useInventory } from '../../context/InventoryContext';

interface DeliveryFormModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DeliveryFormModal: React.FC<DeliveryFormModalProps> = ({ isOpen, onClose }) => {
  const { createDelivery, products, warehouses, showToast } = useInventory();

  const [customer, setCustomer] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [sourceWarehouseId, setSourceWarehouseId] = useState('wh-001');
  const [items, setItems] = useState<{ productId: string; quantity: number }[]>([
    { productId: products[0]?.id || '', quantity: 5 },
  ]);
  const [notes, setNotes] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const handleAddItem = () => {
    setItems((prev) => [...prev, { productId: products[0]?.id || '', quantity: 1 }]);
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!customer.trim()) {
      setErrorMessage('Customer Name is required.');
      return;
    }

    // Validate quantities against available stock in source warehouse
    for (const it of items) {
      const prod = products.find((p) => p.id === it.productId);
      if (!prod) continue;
      const avail = prod.warehouseStock[sourceWarehouseId] || 0;
      if (it.quantity > avail) {
        setErrorMessage(
          `Quantity error for "${prod.name}": Entered ${it.quantity} ${prod.unit}, but only ${avail} ${prod.unit} is available in source warehouse.`
        );
        return;
      }
    }

    const res = createDelivery({
      customer: customer.trim(),
      date,
      sourceWarehouseId,
      items,
      notes: notes.trim(),
    });

    if (!res.success) {
      setErrorMessage(res.message || 'Error creating delivery order.');
      return;
    }

    onClose();
    setCustomer('');
    setDate(new Date().toISOString().split('T')[0]);
    setSourceWarehouseId('wh-001');
    setItems([{ productId: products[0]?.id || '', quantity: 5 }]);
    setNotes('');
    setErrorMessage('');
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Delivery Order (Outgoing)" maxWidth="2xl">
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        {errorMessage && (
          <div className="flex items-start gap-2 p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>{errorMessage}</div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Customer / Client Name *</label>
            <input
              type="text"
              placeholder="e.g. Vardhman Textiles"
              value={customer}
              onChange={(e) => setCustomer(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Dispatch Date *</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Source Warehouse</label>
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
        </div>

        {/* Line Items */}
        <div className="border border-slate-200 rounded-md p-3 bg-slate-50/50 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-slate-800">Dispatch Items</h4>
            <button
              type="button"
              onClick={handleAddItem}
              className="inline-flex items-center gap-1 text-xs font-semibold text-sky-700 hover:text-sky-900"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Product Line
            </button>
          </div>

          {items.map((item, idx) => {
            const selectedProd = products.find((p) => p.id === item.productId);
            const availStock = selectedProd ? selectedProd.warehouseStock[sourceWarehouseId] || 0 : 0;
            const isExceeded = item.quantity > availStock;

            return (
              <div key={idx} className="flex flex-wrap items-center gap-2 bg-white p-2.5 rounded-md border border-slate-200 shadow-xs">
                <div className="flex-1 min-w-[200px]">
                  <label className="text-[10px] text-slate-500 font-medium">Product Item</label>
                  <select
                    value={item.productId}
                    onChange={(e) => handleItemChange(idx, 'productId', e.target.value)}
                    className="w-full rounded border border-slate-300 p-1.5 text-xs"
                  >
                    {products.map((p) => {
                      const whStock = p.warehouseStock[sourceWarehouseId] || 0;
                      return (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.sku}) — Available: {whStock} {p.unit}
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div className="w-32">
                  <div className="flex justify-between items-center text-[10px] text-slate-500 font-medium">
                    <span>Dispatch Qty</span>
                    <span className={`font-semibold ${isExceeded ? 'text-rose-600' : 'text-slate-700'}`}>
                      Max: {availStock}
                    </span>
                  </div>
                  <input
                    type="number"
                    min="1"
                    max={availStock}
                    value={item.quantity}
                    onChange={(e) => handleItemChange(idx, 'quantity', Number(e.target.value))}
                    className={`w-full rounded border p-1.5 text-xs ${
                      isExceeded ? 'border-rose-500 bg-rose-50 text-rose-900' : 'border-slate-300'
                    }`}
                  />
                </div>

                <button
                  type="button"
                  onClick={() => handleRemoveItem(idx)}
                  disabled={items.length === 1}
                  className="mt-4 p-1 text-slate-400 hover:text-rose-600 disabled:opacity-40"
                  title="Remove item"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            );
          })}
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">Notes / Shipping Instructions</label>
          <input
            type="text"
            placeholder="e.g. Sales Order SO-9912, Freight transport details"
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
            className="px-4 py-2 text-xs font-semibold text-white bg-blue-700 rounded-md hover:bg-blue-800 transition-colors shadow-xs"
          >
            Save Draft Delivery Order
          </button>
        </div>
      </form>
    </Modal>
  );
};
