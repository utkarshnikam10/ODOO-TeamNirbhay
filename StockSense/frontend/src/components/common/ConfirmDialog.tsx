import React from 'react';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Modal } from './Modal';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  details?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'primary' | 'danger' | 'warning';
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  details,
  confirmLabel = 'Confirm Action',
  cancelLabel = 'Cancel',
  variant = 'primary',
}) => {
  let btnClass = 'bg-sky-700 hover:bg-sky-800 text-white';
  let icon = <CheckCircle2 className="h-5 w-5 text-sky-600" />;

  if (variant === 'danger') {
    btnClass = 'bg-rose-600 hover:bg-rose-700 text-white';
    icon = <AlertTriangle className="h-5 w-5 text-rose-600" />;
  } else if (variant === 'warning') {
    btnClass = 'bg-amber-600 hover:bg-amber-700 text-white';
    icon = <AlertTriangle className="h-5 w-5 text-amber-600" />;
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} maxWidth="md">
      <div className="flex gap-4">
        <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-slate-100">
          {icon}
        </div>
        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-800">{message}</p>
          {details && (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 font-mono">
              {details}
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100">
        <button
          type="button"
          onClick={onClose}
          className="px-3.5 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors"
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          onClick={() => {
            onConfirm();
            onClose();
          }}
          className={`px-4 py-2 text-xs font-medium rounded-md shadow-xs transition-colors ${btnClass}`}
        >
          {confirmLabel}
        </button>
      </div>
    </Modal>
  );
};
