import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { useInventory } from '../../context/InventoryContext';

interface WarehouseFormModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const WarehouseFormModal: React.FC<WarehouseFormModalProps> = ({ isOpen, onClose }) => {
  const { createWarehouse } = useInventory();

  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [address, setAddress] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = 'Warehouse Name is required.';
    if (!location.trim()) errs.location = 'City / Location is required.';
    if (!address.trim()) errs.address = 'Street Address is required.';

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    createWarehouse({
      name: name.trim(),
      location: location.trim(),
      address: address.trim(),
    });

    onClose();
    setName('');
    setLocation('');
    setAddress('');
    setErrors({});
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add New Warehouse Facility" maxWidth="md">
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div>
          <label className="block font-medium text-slate-700 mb-1">Warehouse Name *</label>
          <input
            type="text"
            placeholder="e.g. Regional Hub Warehouse 3"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
          />
          {errors.name && <p className="mt-1 text-[11px] text-rose-600">{errors.name}</p>}
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">City / Region Location *</label>
          <input
            type="text"
            placeholder="e.g. Amritsar, Punjab"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
          />
          {errors.location && <p className="mt-1 text-[11px] text-rose-600">{errors.location}</p>}
        </div>

        <div>
          <label className="block font-medium text-slate-700 mb-1">Full Street Address *</label>
          <textarea
            rows={2}
            placeholder="Plot number, industrial area, road..."
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
          />
          {errors.address && <p className="mt-1 text-[11px] text-rose-600">{errors.address}</p>}
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
            Create Warehouse
          </button>
        </div>
      </form>
    </Modal>
  );
};
