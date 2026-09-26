import React from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import { useInventory } from '../../context/InventoryContext';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useInventory();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => {
        let icon = <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
        let borderClass = 'border-emerald-200 bg-emerald-50/90 text-emerald-900';

        if (toast.type === 'error') {
          icon = <AlertCircle className="h-4 w-4 text-rose-600" />;
          borderClass = 'border-rose-200 bg-rose-50/90 text-rose-900';
        } else if (toast.type === 'warning') {
          icon = <AlertTriangle className="h-4 w-4 text-amber-600" />;
          borderClass = 'border-amber-200 bg-amber-50/90 text-amber-900';
        } else if (toast.type === 'info') {
          icon = <Info className="h-4 w-4 text-sky-600" />;
          borderClass = 'border-sky-200 bg-sky-50/90 text-sky-900';
        }

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-md border p-3 shadow-md backdrop-blur-xs transition-all animate-in slide-in-from-bottom-5 duration-200 ${borderClass}`}
          >
            <div className="mt-0.5 flex-shrink-0">{icon}</div>
            <div className="flex-1 min-w-0">
              <h4 className="text-xs font-semibold">{toast.title}</h4>
              <p className="mt-0.5 text-xs text-slate-700 leading-snug">{toast.message}</p>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-slate-600 p-0.5 rounded-sm"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
