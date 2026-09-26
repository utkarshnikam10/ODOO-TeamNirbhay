import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'amber' | 'rose' | 'emerald' | 'sky';
  onClick?: () => void;
  active?: boolean;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
  onClick,
  active = false,
}) => {
  let iconBg = 'bg-slate-100 text-slate-600';
  let borderColor = 'border-slate-200 hover:border-slate-300';

  if (variant === 'amber') {
    iconBg = 'bg-amber-100/70 text-amber-700';
    if (active) borderColor = 'border-amber-500 ring-1 ring-amber-500';
  } else if (variant === 'rose') {
    iconBg = 'bg-rose-100/70 text-rose-700';
    if (active) borderColor = 'border-rose-500 ring-1 ring-rose-500';
  } else if (variant === 'emerald') {
    iconBg = 'bg-emerald-100/70 text-emerald-700';
    if (active) borderColor = 'border-emerald-500 ring-1 ring-emerald-500';
  } else if (variant === 'sky') {
    iconBg = 'bg-sky-100/70 text-sky-700';
    if (active) borderColor = 'border-sky-500 ring-1 ring-sky-500';
  }

  return (
    <div
      onClick={onClick}
      className={`relative flex flex-col justify-between rounded-lg border bg-white p-4 shadow-sm transition-all ${
        onClick ? 'cursor-pointer hover:shadow-md' : ''
      } ${borderColor}`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</span>
        <div className={`flex h-9 w-9 items-center justify-center rounded-md ${iconBg}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-bold tracking-tight text-slate-900">{typeof value === 'number' ? value.toLocaleString() : value}</span>
        {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
      </div>
    </div>
  );
};
