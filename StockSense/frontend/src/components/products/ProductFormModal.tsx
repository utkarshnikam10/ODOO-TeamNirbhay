import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { useInventory } from '../../context/InventoryContext';

interface ProductFormModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ProductFormModal: React.FC<ProductFormModalProps> = ({ isOpen, onClose }) => {
  const { createProduct, warehouses, products, showToast } = useInventory();

  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [category, setCategory] = useState('Raw Materials');
  const [unit, setUnit] = useState('kg');
  const [minReorderLevel, setMinReorderLevel] = useState<number>(100);
  const [initialStock, setInitialStock] = useState<number>(0);
  const [warehouseId, setWarehouseId] = useState<string>('wh-001');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = 'Product Name is required.';
    if (!sku.trim()) errs.sku = 'SKU / Code is required.';
    else if (products.some((p) => p.sku.toLowerCase() === sku.trim().toLowerCase())) {
      errs.sku = 'SKU already exists in catalog.';
    }
    if (minReorderLevel < 0) errs.minReorderLevel = 'Reorder level cannot be negative.';
    if (initialStock < 0) errs.initialStock = 'Initial stock cannot be negative.';

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    // Construct warehouse stock map
    const warehouseStock: Record<string, number> = {};
    warehouses.forEach((w) => {
      warehouseStock[w.id] = w.id === warehouseId ? Number(initialStock) : 0;
    });

    createProduct({
      name: name.trim(),
      sku: sku.trim().toUpperCase(),
      category,
      unit,
      minReorderLevel: Number(minReorderLevel),
      warehouseStock,
      description: description.trim(),
    });

    onClose();
    // Reset form
    setName('');
    setSku('');
    setCategory('Raw Materials');
    setUnit('kg');
    setMinReorderLevel(100);
    setInitialStock(0);
    setDescription('');
    setErrors({});
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Product SKU" maxWidth="lg">
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Product Name *</label>
            <input
              type="text"
              placeholder="e.g. Steel Rods 12mm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
            {errors.name && <p className="mt-1 text-[11px] text-rose-600">{errors.name}</p>}
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">SKU / Item Code *</label>
            <input
              type="text"
              placeholder="e.g. RM-008"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs font-mono uppercase focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
            {errors.sku && <p className="mt-1 text-[11px] text-rose-600">{errors.sku}</p>}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            >
              <option value="Raw Materials">Raw Materials</option>
              <option value="Finished Goods">Finished Goods</option>
              <option value="Packaging">Packaging</option>
              <option value="Electrical">Electrical</option>
              <option value="Tools">Tools</option>
              <option value="Safety Equipment">Safety Equipment</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Unit of Measure</label>
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            >
              <option value="kg">kg (Kilogram)</option>
              <option value="meter">meter (Meter)</option>
              <option value="pcs">pcs (Pieces)</option>
              <option value="box">box (Box)</option>
              <option value="set">set (Set)</option>
              <option value="roll">roll (Roll)</option>
              <option value="liter">liter (Liter)</option>
              <option value="pair">pair (Pair)</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Reorder Level Threshold</label>
            <input
              type="number"
              min="0"
              value={minReorderLevel}
              onChange={(e) => setMinReorderLevel(Number(e.target.value))}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
            {errors.minReorderLevel && (
              <p className="mt-1 text-[11px] text-rose-600">{errors.minReorderLevel}</p>
            )}
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Initial Opening Stock</label>
            <input
              type="number"
              min="0"
              value={initialStock}
              onChange={(e) => setInitialStock(Number(e.target.value))}
              className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
            />
            {errors.initialStock && <p className="mt-1 text-[11px] text-rose-600">{errors.initialStock}</p>}
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">Assigned Warehouse</label>
            <select
              value={warehouseId}
              onChange={(e) => setWarehouseId(e.target.value)}
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
          <label className="block font-medium text-slate-700 mb-1">Description / Notes</label>
          <textarea
            rows={3}
            placeholder="Specification notes, material grade, manufacturer info..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
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
            Create Product
          </button>
        </div>
      </form>
    </Modal>
  );
};
