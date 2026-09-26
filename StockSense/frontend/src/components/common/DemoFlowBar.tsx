import React, { useState } from 'react';
import { Play, Sparkles, CheckCircle2, RefreshCw, ChevronRight, Info } from 'lucide-react';
import { useInventory } from '../../context/InventoryContext';

export const DemoFlowBar: React.FC = () => {
  const {
    setActiveView,
    receipts,
    validateReceipt,
    createReceipt,
    products,
    transfers,
    validateTransfer,
    createTransfer,
    deliveries,
    validateDelivery,
    createDelivery,
    createAdjustment,
    showToast,
  } = useInventory();

  const [step, setStep] = useState<number>(0);
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const demoSteps = [
    {
      title: '1. Dashboard Overview',
      description: 'Review operational KPIs (Products, Low Stock, Pending Orders).',
      action: () => setActiveView('dashboard'),
    },
    {
      title: '2. Inspect Product Catalog',
      description: 'View Steel Rods (RM-001) stock breakdown across warehouses.',
      action: () => setActiveView('products'),
    },
    {
      title: '3. Receive Incoming Goods (50 kg Steel Rods)',
      description: 'Trigger validation for inbound receipt REC-1025.',
      action: () => {
        setActiveView('receipts');
        const readyRec = receipts.find((r) => r.status === 'Ready');
        if (readyRec) {
          validateReceipt(readyRec.id);
        } else {
          const steelProd = products.find((p) => p.sku === 'RM-001');
          if (steelProd) {
            createReceipt({
              supplier: 'Tata Steel Direct',
              date: new Date().toISOString().split('T')[0],
              destinationWarehouseId: 'wh-001',
              items: [{ productId: steelProd.id, quantity: 50 }],
              notes: 'Hackathon Quick Demo Receipt',
            });
          }
        }
      },
    },
    {
      title: '4. Internal Warehouse Transfer',
      description: 'Move 20 kg Steel Rods from Main Warehouse -> Production Floor.',
      action: () => {
        setActiveView('transfers');
        const steelProd = products.find((p) => p.sku === 'RM-001');
        if (steelProd) {
          const res = createTransfer({
            sourceWarehouseId: 'wh-001',
            destinationWarehouseId: 'wh-002',
            items: [{ productId: steelProd.id, quantity: 20 }],
            reason: 'Production line supply replenishment',
            date: new Date().toISOString().split('T')[0],
          });
          if (res.transfer) {
            validateTransfer(res.transfer.id);
          }
        }
      },
    },
    {
      title: '5. Dispatch Customer Delivery Order',
      description: 'Validate DO-1048 (10 Ergonomic Chairs dispatched to Vardhman).',
      action: () => {
        setActiveView('deliveries');
        const targetDel = deliveries.find((d) => d.deliveryNo === 'DO-1048');
        if (targetDel) {
          validateDelivery(targetDel.id);
        } else {
          const chair = products.find((p) => p.sku === 'FG-101');
          if (chair) {
            const res = createDelivery({
              customer: 'Vardhman Textiles',
              date: new Date().toISOString().split('T')[0],
              sourceWarehouseId: 'wh-001',
              items: [{ productId: chair.id, quantity: 5 }],
            });
            if (res.delivery) validateDelivery(res.delivery.id);
          }
        }
      },
    },
    {
      title: '6. Perform Physical Stock Audit Adjustment',
      description: 'Adjust WH-001 Steel Sheet stock for cutting scrap loss.',
      action: () => {
        setActiveView('adjustments');
        const steelSheet = products.find((p) => p.sku === 'RM-005');
        if (steelSheet) {
          const sysQty = steelSheet.warehouseStock['wh-001'] || 15;
          createAdjustment({
            warehouseId: 'wh-001',
            productId: steelSheet.id,
            physicalQuantity: Math.max(0, sysQty - 2),
            reason: 'Audit reconciliation scrap loss',
            notes: 'Physical count verified by auditor.',
          });
        }
      },
    },
    {
      title: '7. View Complete Stock Movement Ledger',
      description: 'Inspect full audit trail of all receipts, transfers, and dispatches.',
      action: () => setActiveView('ledger'),
    },
  ];

  const handleNextStep = () => {
    if (step < demoSteps.length) {
      demoSteps[step].action();
      showToast('info', 'Demo Step Executed', demoSteps[step].title);
      setStep((prev) => Math.min(demoSteps.length, prev + 1));
    }
  };

  return (
    <div className="bg-slate-900 text-white border-b border-slate-800 px-4 py-2">
      <div className="mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sky-500/20 text-sky-400 font-bold text-[11px]">
            <Sparkles className="h-3 w-3" />
          </span>
          <span className="font-semibold text-sky-300">Hackathon Jury Demo Guide:</span>
          <span className="text-slate-300 hidden sm:inline">
            {step < demoSteps.length ? demoSteps[step].title : 'Demo Scenario Complete!'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {step < demoSteps.length ? (
            <button
              onClick={handleNextStep}
              className="inline-flex items-center gap-1.5 rounded bg-sky-600 px-3 py-1 text-xs font-semibold text-white hover:bg-sky-500 transition-colors shadow-xs"
            >
              <Play className="h-3 w-3 fill-current" />
              Run Step {step + 1}
            </button>
          ) : (
            <button
              onClick={() => {
                setStep(0);
                setActiveView('dashboard');
              }}
              className="inline-flex items-center gap-1.5 rounded bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors"
            >
              <RefreshCw className="h-3 w-3" />
              Restart Demo Flow
            </button>
          )}

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="text-slate-400 hover:text-white underline text-[11px] ml-2"
          >
            {isOpen ? 'Hide Steps' : 'View All 7 Steps'}
          </button>
        </div>
      </div>

      {/* Expanded Steps Drawer */}
      {isOpen && (
        <div className="mt-2 border-t border-slate-800 pt-2 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          {demoSteps.map((s, idx) => (
            <button
              key={idx}
              onClick={() => {
                setStep(idx);
                s.action();
              }}
              className={`p-2 rounded text-left border transition-colors ${
                idx === step
                  ? 'border-sky-500 bg-sky-950/60 text-sky-200'
                  : idx < step
                  ? 'border-emerald-800/80 bg-slate-800/40 text-emerald-400'
                  : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="text-[10px] font-bold flex items-center justify-between">
                <span>Step {idx + 1}</span>
                {idx < step && <CheckCircle2 className="h-3 w-3 text-emerald-400" />}
              </div>
              <div className="text-xs font-semibold truncate mt-0.5">{s.title.split('. ')[1] || s.title}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
