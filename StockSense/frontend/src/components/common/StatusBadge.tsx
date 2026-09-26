import React from 'react';
import { DocumentStatus, StockStatus } from '../../types';

interface StatusBadgeProps {
  status: DocumentStatus | StockStatus | 'Active' | 'Inactive' | 'Validated' | 'Dispatched' | 'Completed' | 'Adjusted' | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  switch (status) {
    // Document Statuses
    case 'Draft':
      colorClasses = 'bg-slate-100 text-slate-700 border-slate-300';
      break;
    case 'Waiting':
      colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
      break;
    case 'Ready':
      colorClasses = 'bg-blue-50 text-blue-700 border-blue-200';
      break;
    case 'Done':
    case 'Validated':
    case 'Dispatched':
    case 'Completed':
    case 'Adjusted':
    case 'Active':
      colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      break;
    case 'Canceled':
    case 'Inactive':
      colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
      break;

    // Stock Statuses
    case 'In Stock':
      colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      break;
    case 'Low Stock':
      colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 font-semibold';
      break;
    case 'Out of Stock':
      colorClasses = 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
      break;
    default:
      colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border ${sizeClasses} ${colorClasses} capitalize transition-colors`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          status === 'Done' || status === 'Active' || status === 'In Stock' || status === 'Validated' || status === 'Completed'
            ? 'bg-emerald-500'
            : status === 'Waiting' || status === 'Low Stock'
            ? 'bg-amber-500'
            : status === 'Ready'
            ? 'bg-blue-500'
            : status === 'Out of Stock' || status === 'Canceled'
            ? 'bg-rose-500'
            : 'bg-slate-400'
        }`}
      />
      {status}
    </span>
  );
};
