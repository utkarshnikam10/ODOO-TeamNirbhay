import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useInventory } from '../../context/InventoryContext';

export const AnalyticsCharts: React.FC = () => {
  const { products, warehouses, stockLedger } = useInventory();

  // 1. Stock Movement (Incoming vs Outgoing) over last 7 days simulation based on ledger
  const movementData = [
    { date: 'Sep 20', Incoming: 540, Outgoing: 200, Adjustments: -1 },
    { date: 'Sep 21', Incoming: 80, Outgoing: 120, Adjustments: 5 },
    { date: 'Sep 22', Incoming: 0, Outgoing: 20, Adjustments: 0 },
    { date: 'Sep 23', Incoming: 0, Outgoing: 150, Adjustments: -1 },
    { date: 'Sep 24', Incoming: 850, Outgoing: 300, Adjustments: -3 },
    { date: 'Sep 25', Incoming: 25, Outgoing: 60, Adjustments: -1 },
    { date: 'Sep 26', Incoming: 120, Outgoing: 40, Adjustments: -3 },
  ];

  // 2. Inventory stock by Category
  const categoryStockMap: Record<string, number> = {};
  products.forEach((p) => {
    const total = Object.values(p.warehouseStock || {}).reduce((a, b) => a + b, 0);
    categoryStockMap[p.category] = (categoryStockMap[p.category] || 0) + total;
  });

  const categoryData = Object.entries(categoryStockMap).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = ['#0284c7', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#64748b'];

  // 3. Warehouse Stock Distribution
  const warehouseData = warehouses.map((w) => {
    const totalUnits = products.reduce((sum, p) => sum + (p.warehouseStock[w.id] || 0), 0);
    return {
      name: w.name,
      code: w.code,
      units: totalUnits,
    };
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Chart 1: Stock Movement */}
      <div className="lg:col-span-2 rounded-lg border border-slate-200 bg-white p-4 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Stock Movement Trends</h3>
            <p className="text-xs text-slate-500">Incoming Receipts vs Outgoing Deliveries (Last 7 Days)</p>
          </div>
          <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
            Units (kg / pcs)
          </span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={movementData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#1e293b',
                  borderRadius: '6px',
                  color: '#ffffff',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="Incoming" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Outgoing" fill="#0284c7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: Inventory by Category */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs flex flex-col justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Inventory by Category</h3>
          <p className="text-xs text-slate-500">Total units stored per product category</p>
        </div>
        <div className="h-56 w-full flex items-center justify-center my-2">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={75}
                paddingAngle={3}
                dataKey="value"
              >
                {categoryData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#1e293b',
                  borderRadius: '6px',
                  color: '#ffffff',
                  fontSize: '12px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-1 border-t border-slate-100 pt-2 text-[11px]">
          {categoryData.map((cat, idx) => (
            <div key={cat.name} className="flex items-center gap-1.5 truncate">
              <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
              <span className="text-slate-600 truncate">{cat.name}:</span>
              <span className="font-semibold text-slate-900">{cat.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
