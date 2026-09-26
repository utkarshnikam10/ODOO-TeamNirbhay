import React from 'react';
import { History, ArrowDownLeft, ArrowUpRight, ArrowRightLeft, SlidersHorizontal } from 'lucide-react';
import { useInventory } from '../../context/InventoryContext';

export const RecentActivityFeed: React.FC = () => {
  const { stockLedger, setActiveView } = useInventory();

  const recentLedger = stockLedger.slice(0, 7);

  const getIcon = (type: string) => {
    switch (type) {
      case 'Receipt':
        return <ArrowDownLeft className="h-3.5 w-3.5 text-emerald-600" />;
      case 'Delivery':
        return <ArrowUpRight className="h-3.5 w-3.5 text-blue-600" />;
      case 'Transfer':
        return <ArrowRightLeft className="h-3.5 w-3.5 text-amber-600" />;
      case 'Adjustment':
        return <SlidersHorizontal className="h-3.5 w-3.5 text-purple-600" />;
      default:
        return <History className="h-3.5 w-3.5 text-slate-500" />;
    }
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-slate-500" />
            <h3 className="text-sm font-bold text-slate-900">Recent Activity Feed</h3>
          </div>
          <button
            onClick={() => setActiveView('ledger')}
            className="text-xs font-medium text-sky-700 hover:text-sky-900"
          >
            Full Audit Log
          </button>
        </div>

        <div className="space-y-3">
          {recentLedger.map((item) => (
            <div key={item.id} className="flex items-start gap-2.5 text-xs">
              <div className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-slate-100">
                {getIcon(item.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900">{item.referenceNo}</span>
                  <span className="text-[10px] text-slate-400">{item.timestamp.split(' ')[1] || item.timestamp}</span>
                </div>
                <p className="text-slate-600 truncate mt-0.5">
                  <span className="font-medium text-slate-800">{item.type}</span>: {item.productName} (
                  <span className={`font-bold ${item.quantity > 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                    {item.quantity > 0 ? `+${item.quantity}` : item.quantity}
                  </span>
                  )
                </p>
                <div className="text-[10px] text-slate-400 truncate">
                  By {item.performedBy} • {item.warehouseName}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
