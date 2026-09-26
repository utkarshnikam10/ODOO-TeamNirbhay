import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  Product,
  Warehouse,
  Receipt,
  DeliveryOrder,
  InternalTransfer,
  InventoryAdjustment,
  StockLedgerEntry,
  AppNotification,
  ToastMessage,
  User,
  ViewType,
  SmartReorderSuggestion,
} from '../types';
import {
  INITIAL_PRODUCTS,
  INITIAL_WAREHOUSES,
  INITIAL_RECEIPTS,
  INITIAL_DELIVERIES,
  INITIAL_TRANSFERS,
  INITIAL_ADJUSTMENTS,
  INITIAL_LEDGER,
  INITIAL_NOTIFICATIONS,
  INITIAL_USER,
} from '../data/mockData';

interface KpiStats {
  totalProductsCount: number;
  totalUnitsInStock: number;
  lowStockCount: number;
  outOfStockCount: number;
  pendingReceiptsCount: number;
  pendingDeliveriesCount: number;
  internalTransfersCount: number;
}

interface InventoryContextType {
  activeView: ViewType;
  setActiveView: (view: ViewType) => void;
  selectedWarehouseFilter: string;
  setSelectedWarehouseFilter: (whId: string) => void;
  products: Product[];
  warehouses: Warehouse[];
  receipts: Receipt[];
  deliveries: DeliveryOrder[];
  transfers: InternalTransfer[];
  adjustments: InventoryAdjustment[];
  stockLedger: StockLedgerEntry[];
  notifications: AppNotification[];
  toasts: ToastMessage[];
  currentUser: User;
  kpiStats: KpiStats;
  
  // Actions
  createProduct: (product: Omit<Product, 'id' | 'createdAt'>) => void;
  updateProduct: (id: string, productData: Partial<Product>) => void;
  createReceipt: (receiptData: { supplier: string; date: string; destinationWarehouseId: string; items: { productId: string; quantity: number; unitPrice?: number }[]; notes?: string }) => void;
  validateReceipt: (receiptId: string) => { success: boolean; message: string };
  cancelReceipt: (receiptId: string) => void;
  createDelivery: (deliveryData: { customer: string; date: string; sourceWarehouseId: string; items: { productId: string; quantity: number }[]; notes?: string }) => { success: boolean; message?: string; delivery?: DeliveryOrder };
  validateDelivery: (deliveryId: string) => { success: boolean; message: string };
  cancelDelivery: (deliveryId: string) => void;
  createTransfer: (transferData: { sourceWarehouseId: string; destinationWarehouseId: string; items: { productId: string; quantity: number }[]; reason: string; date: string }) => { success: boolean; message?: string; transfer?: InternalTransfer };
  validateTransfer: (transferId: string) => { success: boolean; message: string };
  cancelTransfer: (transferId: string) => void;
  createAdjustment: (adjData: { warehouseId: string; productId: string; physicalQuantity: number; reason: string; notes?: string }) => { success: boolean; message: string };
  createWarehouse: (whData: { name: string; location: string; address: string }) => void;
  updateWarehouse: (id: string, data: Partial<Warehouse>) => void;
  toggleWarehouseStatus: (id: string) => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  showToast: (type: ToastMessage['type'], title: string, message: string) => void;
  removeToast: (id: string) => void;
  getSmartReorderSuggestions: () => SmartReorderSuggestion[];
  quickReorderProduct: (productId: string, qty: number, targetWarehouseId: string) => void;
  resetToDefaultData: () => void;
}

const InventoryContext = createContext<InventoryContextType | undefined>(undefined);

const LOCAL_STORAGE_KEY = 'stocksense_inventory_data_v1';

export const InventoryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeView, setActiveView] = useState<ViewType>('dashboard');
  const [selectedWarehouseFilter, setSelectedWarehouseFilter] = useState<string>('all');
  
  // State variables loaded from localStorage or initialized
  const [products, setProducts] = useState<Product[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_products`);
    return saved ? JSON.parse(saved) : INITIAL_PRODUCTS;
  });

  const [warehouses, setWarehouses] = useState<Warehouse[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_warehouses`);
    return saved ? JSON.parse(saved) : INITIAL_WAREHOUSES;
  });

  const [receipts, setReceipts] = useState<Receipt[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_receipts`);
    return saved ? JSON.parse(saved) : INITIAL_RECEIPTS;
  });

  const [deliveries, setDeliveries] = useState<DeliveryOrder[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_deliveries`);
    return saved ? JSON.parse(saved) : INITIAL_DELIVERIES;
  });

  const [transfers, setTransfers] = useState<InternalTransfer[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_transfers`);
    return saved ? JSON.parse(saved) : INITIAL_TRANSFERS;
  });

  const [adjustments, setAdjustments] = useState<InventoryAdjustment[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_adjustments`);
    return saved ? JSON.parse(saved) : INITIAL_ADJUSTMENTS;
  });

  const [stockLedger, setStockLedger] = useState<StockLedgerEntry[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_ledger`);
    return saved ? JSON.parse(saved) : INITIAL_LEDGER;
  });

  const [notifications, setNotifications] = useState<AppNotification[]>(() => {
    const saved = localStorage.getItem(`${LOCAL_STORAGE_KEY}_notifications`);
    return saved ? JSON.parse(saved) : INITIAL_NOTIFICATIONS;
  });

  const [currentUser] = useState<User>(INITIAL_USER);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Persist state to localStorage on changes
  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_products`, JSON.stringify(products));
  }, [products]);

  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_warehouses`, JSON.stringify(warehouses));
  }, [warehouses]);

  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_receipts`, JSON.stringify(receipts));
  }, [receipts]);

  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_deliveries`, JSON.stringify(deliveries));
  }, [deliveries]);

  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_transfers`, JSON.stringify(transfers));
  }, [transfers]);

  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_adjustments`, JSON.stringify(adjustments));
  }, [adjustments]);

  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_ledger`, JSON.stringify(stockLedger));
  }, [stockLedger]);

  useEffect(() => {
    localStorage.setItem(`${LOCAL_STORAGE_KEY}_notifications`, JSON.stringify(notifications));
  }, [notifications]);

  // Toast notification helper
  const showToast = (type: ToastMessage['type'], title: string, message: string) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      removeToast(id);
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Notification helpers
  const addNotification = (
    type: AppNotification['type'],
    title: string,
    message: string,
    linkView?: ViewType,
    linkId?: string
  ) => {
    const newNotif: AppNotification = {
      id: `notif-${Date.now()}`,
      type,
      title,
      message,
      timestamp: 'Just now',
      read: false,
      linkView,
      linkId,
    };
    setNotifications((prev) => [newNotif, ...prev]);
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  // Derived KPI statistics
  const calculateKpiStats = (): KpiStats => {
    let totalUnits = 0;
    let lowStock = 0;
    let outOfStock = 0;

    products.forEach((p) => {
      const prodTotal = Object.values(p.warehouseStock || {}).reduce((a, b) => a + b, 0);
      totalUnits += prodTotal;
      if (prodTotal === 0) {
        outOfStock++;
      } else if (prodTotal <= p.minReorderLevel) {
        lowStock++;
      }
    });

    const pendingReceipts = receipts.filter((r) => r.status === 'Waiting' || r.status === 'Ready' || r.status === 'Draft').length;
    const pendingDeliveries = deliveries.filter((d) => d.status === 'Waiting' || d.status === 'Ready' || d.status === 'Draft').length;
    const internalTransfersCount = transfers.filter((t) => t.status === 'Draft' || t.status === 'Ready' || t.status === 'Done').length;

    return {
      totalProductsCount: products.length,
      totalUnitsInStock: totalUnits,
      lowStockCount: lowStock,
      outOfStockCount: outOfStock,
      pendingReceiptsCount: pendingReceipts,
      pendingDeliveriesCount: pendingDeliveries,
      internalTransfersCount: internalTransfersCount,
    };
  };

  const kpiStats = calculateKpiStats();

  // Create Product
  const createProduct = (productData: Omit<Product, 'id' | 'createdAt'>) => {
    const newId = `prod-${Date.now()}`;
    const newProduct: Product = {
      ...productData,
      id: newId,
      createdAt: new Date().toISOString().split('T')[0],
    };
    setProducts((prev) => [newProduct, ...prev]);
    showToast('success', 'Product Created', `Product "${newProduct.name}" (${newProduct.sku}) added successfully.`);
  };

  // Update Product
  const updateProduct = (id: string, productData: Partial<Product>) => {
    setProducts((prev) => prev.map((p) => (p.id === id ? { ...p, ...productData } : p)));
    showToast('success', 'Product Updated', 'Product details saved successfully.');
  };

  // Create Receipt
  const createReceipt = (receiptData: {
    supplier: string;
    date: string;
    destinationWarehouseId: string;
    items: { productId: string; quantity: number; unitPrice?: number }[];
    notes?: string;
  }) => {
    const receiptNum = `REC-${1030 + receipts.length}`;
    const newReceipt: Receipt = {
      id: `rec-${Date.now()}`,
      receiptNo: receiptNum,
      supplier: receiptData.supplier,
      date: receiptData.date,
      destinationWarehouseId: receiptData.destinationWarehouseId,
      items: receiptData.items,
      status: 'Draft',
      notes: receiptData.notes,
      createdBy: currentUser.name,
    };

    setReceipts((prev) => [newReceipt, ...prev]);
    showToast('success', 'Receipt Draft Created', `${receiptNum} created in Draft status.`);
    addNotification('receipt', 'New Receipt Created', `${receiptNum} from ${receiptData.supplier} added to Drafts.`, 'receipts', newReceipt.id);
  };

  // Validate Receipt (Increases inventory stock + creates ledger entry)
  const validateReceipt = (receiptId: string): { success: boolean; message: string } => {
    const targetReceipt = receipts.find((r) => r.id === receiptId);
    if (!targetReceipt) return { success: false, message: 'Receipt not found.' };
    if (targetReceipt.status === 'Done') return { success: false, message: 'Receipt is already validated.' };
    if (targetReceipt.status === 'Canceled') return { success: false, message: 'Cannot validate a canceled receipt.' };

    const targetWh = warehouses.find((w) => w.id === targetReceipt.destinationWarehouseId);
    const whName = targetWh ? targetWh.name : 'Target Warehouse';
    const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

    const newLedgerEntries: StockLedgerEntry[] = [];
    const updatedProducts = [...products];

    targetReceipt.items.forEach((item) => {
      const prodIndex = updatedProducts.findIndex((p) => p.id === item.productId);
      if (prodIndex !== -1) {
        const prod = updatedProducts[prodIndex];
        const currentWhStock = prod.warehouseStock[targetReceipt.destinationWarehouseId] || 0;
        const newWhStock = currentWhStock + item.quantity;

        const updatedWhStock = {
          ...prod.warehouseStock,
          [targetReceipt.destinationWarehouseId]: newWhStock,
        };

        updatedProducts[prodIndex] = {
          ...prod,
          warehouseStock: updatedWhStock,
        };

        const totalBefore = Object.values(prod.warehouseStock).reduce((a, b) => a + b, 0);

        newLedgerEntries.push({
          id: `led-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
          timestamp: now,
          referenceNo: targetReceipt.receiptNo,
          type: 'Receipt',
          productId: prod.id,
          productName: prod.name,
          sku: prod.sku,
          warehouseId: targetReceipt.destinationWarehouseId,
          warehouseName: whName,
          fromLocation: `Vendor: ${targetReceipt.supplier}`,
          toLocation: `${targetWh?.code || ''} (${whName})`,
          quantity: item.quantity,
          beforeStock: totalBefore,
          afterStock: totalBefore + item.quantity,
          performedBy: currentUser.name,
          status: 'Validated',
        });
      }
    });

    setProducts(updatedProducts);
    setStockLedger((prev) => [...newLedgerEntries, ...prev]);
    setReceipts((prev) => prev.map((r) => (r.id === receiptId ? { ...r, status: 'Done' } : r)));

    const successMsg = `Receipt ${targetReceipt.receiptNo} validated. Stock updated in ${whName}.`;
    showToast('success', 'Receipt Validated', successMsg);
    addNotification('receipt', 'Receipt Validated', successMsg, 'receipts', receiptId);

    return { success: true, message: successMsg };
  };

  const cancelReceipt = (receiptId: string) => {
    setReceipts((prev) => prev.map((r) => (r.id === receiptId ? { ...r, status: 'Canceled' } : r)));
    showToast('info', 'Receipt Canceled', 'Receipt status changed to Canceled.');
  };

  // Create Delivery Order
  const createDelivery = (deliveryData: {
    customer: string;
    date: string;
    sourceWarehouseId: string;
    items: { productId: string; quantity: number }[];
    notes?: string;
  }): { success: boolean; message?: string; delivery?: DeliveryOrder } => {
    // Check available stock
    for (const item of deliveryData.items) {
      const prod = products.find((p) => p.id === item.productId);
      if (!prod) return { success: false, message: 'Product not found.' };
      const availStock = prod.warehouseStock[deliveryData.sourceWarehouseId] || 0;
      if (item.quantity > availStock) {
        return {
          success: false,
          message: `Insufficient stock for "${prod.name}" in source warehouse. Available: ${availStock} ${prod.unit}, Requested: ${item.quantity} ${prod.unit}.`,
        };
      }
    }

    const deliveryNum = `DO-${1050 + deliveries.length}`;
    const newDelivery: DeliveryOrder = {
      id: `del-${Date.now()}`,
      deliveryNo: deliveryNum,
      customer: deliveryData.customer,
      date: deliveryData.date,
      sourceWarehouseId: deliveryData.sourceWarehouseId,
      items: deliveryData.items,
      status: 'Draft',
      notes: deliveryData.notes,
      createdBy: currentUser.name,
    };

    setDeliveries((prev) => [newDelivery, ...prev]);
    showToast('success', 'Delivery Order Created', `${deliveryNum} created in Draft status.`);
    addNotification('delivery', 'New Delivery Order', `${deliveryNum} for ${deliveryData.customer} created.`, 'deliveries', newDelivery.id);

    return { success: true, message: `${deliveryNum} created successfully.`, delivery: newDelivery };
  };

  // Validate Delivery (Decreases stock + logs ledger entry)
  const validateDelivery = (deliveryId: string): { success: boolean; message: string } => {
    const targetDelivery = deliveries.find((d) => d.id === deliveryId);
    if (!targetDelivery) return { success: false, message: 'Delivery Order not found.' };
    if (targetDelivery.status === 'Done') return { success: false, message: 'Delivery Order is already validated.' };
    if (targetDelivery.status === 'Canceled') return { success: false, message: 'Cannot validate a canceled delivery order.' };

    const sourceWh = warehouses.find((w) => w.id === targetDelivery.sourceWarehouseId);
    const whName = sourceWh ? sourceWh.name : 'Source Warehouse';

    // Verify stock availability
    for (const item of targetDelivery.items) {
      const prod = products.find((p) => p.id === item.productId);
      const currentWhStock = prod ? prod.warehouseStock[targetDelivery.sourceWarehouseId] || 0 : 0;
      if (item.quantity > currentWhStock) {
        return {
          success: false,
          message: `Validation failed: Insufficient stock for "${prod?.name || 'Product'}". Available: ${currentWhStock}, Required: ${item.quantity}.`,
        };
      }
    }

    const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const newLedgerEntries: StockLedgerEntry[] = [];
    const updatedProducts = [...products];

    targetDelivery.items.forEach((item) => {
      const prodIndex = updatedProducts.findIndex((p) => p.id === item.productId);
      if (prodIndex !== -1) {
        const prod = updatedProducts[prodIndex];
        const currentWhStock = prod.warehouseStock[targetDelivery.sourceWarehouseId] || 0;
        const newWhStock = Math.max(0, currentWhStock - item.quantity);

        const updatedWhStock = {
          ...prod.warehouseStock,
          [targetDelivery.sourceWarehouseId]: newWhStock,
        };

        updatedProducts[prodIndex] = {
          ...prod,
          warehouseStock: updatedWhStock,
        };

        const totalBefore = Object.values(prod.warehouseStock).reduce((a, b) => a + b, 0);

        newLedgerEntries.push({
          id: `led-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
          timestamp: now,
          referenceNo: targetDelivery.deliveryNo,
          type: 'Delivery',
          productId: prod.id,
          productName: prod.name,
          sku: prod.sku,
          warehouseId: targetDelivery.sourceWarehouseId,
          warehouseName: whName,
          fromLocation: `${sourceWh?.code || ''} (${whName})`,
          toLocation: `Customer: ${targetDelivery.customer}`,
          quantity: -item.quantity,
          beforeStock: totalBefore,
          afterStock: totalBefore - item.quantity,
          performedBy: currentUser.name,
          status: 'Dispatched',
        });
      }
    });

    setProducts(updatedProducts);
    setStockLedger((prev) => [...newLedgerEntries, ...prev]);
    setDeliveries((prev) => prev.map((d) => (d.id === deliveryId ? { ...d, status: 'Done' } : d)));

    const successMsg = `Delivery ${targetDelivery.deliveryNo} validated and dispatched. ${targetDelivery.items.reduce((a, b) => a + b.quantity, 0)} units removed from ${whName}.`;
    showToast('success', 'Delivery Validated', successMsg);
    addNotification('delivery', 'Delivery Dispatched', successMsg, 'deliveries', deliveryId);

    return { success: true, message: successMsg };
  };

  const cancelDelivery = (deliveryId: string) => {
    setDeliveries((prev) => prev.map((d) => (d.id === deliveryId ? { ...d, status: 'Canceled' } : d)));
    showToast('info', 'Delivery Canceled', 'Delivery status changed to Canceled.');
  };

  // Create Internal Transfer
  const createTransfer = (transferData: {
    sourceWarehouseId: string;
    destinationWarehouseId: string;
    items: { productId: string; quantity: number }[];
    reason: string;
    date: string;
  }): { success: boolean; message?: string; transfer?: InternalTransfer } => {
    if (transferData.sourceWarehouseId === transferData.destinationWarehouseId) {
      return { success: false, message: 'Source and destination warehouses cannot be identical.' };
    }

    for (const item of transferData.items) {
      const prod = products.find((p) => p.id === item.productId);
      const availStock = prod ? prod.warehouseStock[transferData.sourceWarehouseId] || 0 : 0;
      if (item.quantity > availStock) {
        return {
          success: false,
          message: `Cannot transfer ${item.quantity} units of "${prod?.name}". Available stock in source warehouse: ${availStock}.`,
        };
      }
    }

    const transferNum = `TR-${210 + transfers.length}`;
    const newTransfer: InternalTransfer = {
      id: `tr-${Date.now()}`,
      transferNo: transferNum,
      date: transferData.date,
      sourceWarehouseId: transferData.sourceWarehouseId,
      destinationWarehouseId: transferData.destinationWarehouseId,
      items: transferData.items,
      reason: transferData.reason,
      status: 'Draft',
      createdBy: currentUser.name,
    };

    setTransfers((prev) => [newTransfer, ...prev]);
    showToast('success', 'Transfer Created', `${transferNum} draft created.`);
    addNotification('transfer', 'New Stock Transfer Draft', `${transferNum} created.`, 'transfers', newTransfer.id);

    return { success: true, message: `${transferNum} created successfully.`, transfer: newTransfer };
  };

  // Validate Internal Transfer (Decreases source stock, Increases dest stock)
  const validateTransfer = (transferId: string): { success: boolean; message: string } => {
    const targetTransfer = transfers.find((t) => t.id === transferId);
    if (!targetTransfer) return { success: false, message: 'Transfer record not found.' };
    if (targetTransfer.status === 'Done') return { success: false, message: 'Transfer is already completed.' };
    if (targetTransfer.status === 'Canceled') return { success: false, message: 'Cannot validate a canceled transfer.' };

    const sourceWh = warehouses.find((w) => w.id === targetTransfer.sourceWarehouseId);
    const destWh = warehouses.find((w) => w.id === targetTransfer.destinationWarehouseId);
    const srcWhName = sourceWh ? sourceWh.name : 'Source WH';
    const destWhName = destWh ? destWh.name : 'Destination WH';

    // Verify stock availability
    for (const item of targetTransfer.items) {
      const prod = products.find((p) => p.id === item.productId);
      const currentSrcStock = prod ? prod.warehouseStock[targetTransfer.sourceWarehouseId] || 0 : 0;
      if (item.quantity > currentSrcStock) {
        return {
          success: false,
          message: `Insufficient stock for "${prod?.name}" in ${srcWhName}. Available: ${currentSrcStock}, Required: ${item.quantity}.`,
        };
      }
    }

    const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const newLedgerEntries: StockLedgerEntry[] = [];
    const updatedProducts = [...products];

    targetTransfer.items.forEach((item) => {
      const prodIndex = updatedProducts.findIndex((p) => p.id === item.productId);
      if (prodIndex !== -1) {
        const prod = updatedProducts[prodIndex];
        const srcStock = prod.warehouseStock[targetTransfer.sourceWarehouseId] || 0;
        const destStock = prod.warehouseStock[targetTransfer.destinationWarehouseId] || 0;

        const updatedWhStock = {
          ...prod.warehouseStock,
          [targetTransfer.sourceWarehouseId]: Math.max(0, srcStock - item.quantity),
          [targetTransfer.destinationWarehouseId]: destStock + item.quantity,
        };

        updatedProducts[prodIndex] = {
          ...prod,
          warehouseStock: updatedWhStock,
        };

        const totalStock = Object.values(prod.warehouseStock).reduce((a, b) => a + b, 0);

        // Record source reduction entry
        newLedgerEntries.push({
          id: `led-${Date.now()}-out`,
          timestamp: now,
          referenceNo: targetTransfer.transferNo,
          type: 'Transfer',
          productId: prod.id,
          productName: prod.name,
          sku: prod.sku,
          warehouseId: targetTransfer.sourceWarehouseId,
          warehouseName: srcWhName,
          fromLocation: `${sourceWh?.code || ''} (${srcWhName})`,
          toLocation: `${destWh?.code || ''} (${destWhName})`,
          quantity: -item.quantity,
          beforeStock: totalStock,
          afterStock: totalStock,
          performedBy: currentUser.name,
          status: 'Completed',
        });

        // Record destination increase entry
        newLedgerEntries.push({
          id: `led-${Date.now()}-in`,
          timestamp: now,
          referenceNo: targetTransfer.transferNo,
          type: 'Transfer',
          productId: prod.id,
          productName: prod.name,
          sku: prod.sku,
          warehouseId: targetTransfer.destinationWarehouseId,
          warehouseName: destWhName,
          fromLocation: `${sourceWh?.code || ''} (${srcWhName})`,
          toLocation: `${destWh?.code || ''} (${destWhName})`,
          quantity: item.quantity,
          beforeStock: totalStock,
          afterStock: totalStock,
          performedBy: currentUser.name,
          status: 'Completed',
        });
      }
    });

    setProducts(updatedProducts);
    setStockLedger((prev) => [...newLedgerEntries, ...prev]);
    setTransfers((prev) => prev.map((t) => (t.id === transferId ? { ...t, status: 'Done' } : t)));

    const successMsg = `Transfer ${targetTransfer.transferNo} validated! Stock moved from ${srcWhName} to ${destWhName}.`;
    showToast('success', 'Transfer Completed', successMsg);
    addNotification('transfer', 'Transfer Completed', successMsg, 'transfers', transferId);

    return { success: true, message: successMsg };
  };

  const cancelTransfer = (transferId: string) => {
    setTransfers((prev) => prev.map((t) => (t.id === transferId ? { ...t, status: 'Canceled' } : t)));
    showToast('info', 'Transfer Canceled', 'Transfer status changed to Canceled.');
  };

  // Create Inventory Adjustment
  const createAdjustment = (adjData: {
    warehouseId: string;
    productId: string;
    physicalQuantity: number;
    reason: string;
    notes?: string;
  }): { success: boolean; message: string } => {
    const prodIndex = products.findIndex((p) => p.id === adjData.productId);
    if (prodIndex === -1) return { success: false, message: 'Product not found.' };

    const targetWh = warehouses.find((w) => w.id === adjData.warehouseId);
    if (!targetWh) return { success: false, message: 'Warehouse not found.' };

    const prod = products[prodIndex];
    const systemQty = prod.warehouseStock[adjData.warehouseId] || 0;
    const diff = adjData.physicalQuantity - systemQty;

    const adjNum = `ADJ-${510 + adjustments.length}`;
    const today = new Date().toISOString().split('T')[0];

    const newAdjustment: InventoryAdjustment = {
      id: `adj-${Date.now()}`,
      adjustmentNo: adjNum,
      date: today,
      warehouseId: adjData.warehouseId,
      productId: adjData.productId,
      systemQuantity: systemQty,
      physicalQuantity: adjData.physicalQuantity,
      difference: diff,
      reason: adjData.reason,
      notes: adjData.notes,
      status: 'Completed',
      createdBy: currentUser.name,
    };

    // Update Product Stock to Physical Count
    const updatedProducts = [...products];
    updatedProducts[prodIndex] = {
      ...prod,
      warehouseStock: {
        ...prod.warehouseStock,
        [adjData.warehouseId]: adjData.physicalQuantity,
      },
    };

    // Record Stock Ledger Entry
    const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const beforeTotal = Object.values(prod.warehouseStock).reduce((a, b) => a + b, 0);

    const ledgerEntry: StockLedgerEntry = {
      id: `led-${Date.now()}`,
      timestamp: now,
      referenceNo: adjNum,
      type: 'Adjustment',
      productId: prod.id,
      productName: prod.name,
      sku: prod.sku,
      warehouseId: adjData.warehouseId,
      warehouseName: targetWh.name,
      fromLocation: `System Qty: ${systemQty}`,
      toLocation: `Physical Audit: ${adjData.physicalQuantity}`,
      quantity: diff,
      beforeStock: beforeTotal,
      afterStock: beforeTotal + diff,
      performedBy: currentUser.name,
      status: 'Adjusted',
    };

    setProducts(updatedProducts);
    setAdjustments((prev) => [newAdjustment, ...prev]);
    setStockLedger((prev) => [ledgerEntry, ...prev]);

    const msg = `Inventory adjusted successfully for "${prod.name}". Stock set to ${adjData.physicalQuantity} (Variance: ${diff > 0 ? `+${diff}` : diff}).`;
    showToast('success', 'Adjustment Applied', msg);
    addNotification('adjustment', 'Stock Adjustment Executed', msg, 'adjustments', newAdjustment.id);

    return { success: true, message: msg };
  };

  // Warehouse Management
  const createWarehouse = (whData: { name: string; location: string; address: string }) => {
    const code = `WH-00${warehouses.length + 1}`;
    const newWh: Warehouse = {
      id: `wh-${Date.now()}`,
      code,
      name: whData.name,
      location: whData.location,
      address: whData.address,
      status: 'Active',
    };
    setWarehouses((prev) => [...prev, newWh]);
    showToast('success', 'Warehouse Created', `Warehouse "${whData.name}" (${code}) added.`);
  };

  const updateWarehouse = (id: string, data: Partial<Warehouse>) => {
    setWarehouses((prev) => prev.map((w) => (w.id === id ? { ...w, ...data } : w)));
    showToast('success', 'Warehouse Updated', 'Warehouse details saved.');
  };

  const toggleWarehouseStatus = (id: string) => {
    setWarehouses((prev) =>
      prev.map((w) => {
        if (w.id === id) {
          const nextStatus = w.status === 'Active' ? 'Inactive' : 'Active';
          showToast('info', 'Warehouse Status Changed', `Warehouse "${w.name}" set to ${nextStatus}.`);
          return { ...w, status: nextStatus };
        }
        return w;
      })
    );
  };

  // Smart Reorder Suggestions logic
  const getSmartReorderSuggestions = (): SmartReorderSuggestion[] => {
    const suggestions: SmartReorderSuggestion[] = [];

    products.forEach((p) => {
      const totalStock = Object.values(p.warehouseStock || {}).reduce((a, b) => a + b, 0);
      if (totalStock <= p.minReorderLevel) {
        // Find warehouse with lowest stock for reorder destination
        let primaryWhId = 'wh-001';
        let lowestQty = Infinity;
        Object.entries(p.warehouseStock || {}).forEach(([whId, qty]) => {
          if (qty < lowestQty) {
            lowestQty = qty;
            primaryWhId = whId;
          }
        });

        const targetWh = warehouses.find((w) => w.id === primaryWhId);
        const suggested = Math.max(p.minReorderLevel * 2, (p.minReorderLevel - totalStock) + (p.minReorderLevel * 2));

        suggestions.push({
          product: p,
          currentStock: totalStock,
          reorderLevel: p.minReorderLevel,
          suggestedQty: suggested,
          reason: totalStock === 0 ? 'Out of stock! Critical zero inventory level.' : `Current stock (${totalStock} ${p.unit}) is below reorder threshold (${p.minReorderLevel} ${p.unit}).`,
          primaryWarehouseId: primaryWhId,
          primaryWarehouseName: targetWh ? targetWh.name : 'Main Warehouse',
        });
      }
    });

    return suggestions;
  };

  // Quick Reorder Action from low stock suggestions
  const quickReorderProduct = (productId: string, qty: number, targetWarehouseId: string) => {
    const prod = products.find((p) => p.id === productId);
    if (!prod) return;

    createReceipt({
      supplier: 'Automated Vendor Dispatch',
      date: new Date().toISOString().split('T')[0],
      destinationWarehouseId: targetWarehouseId,
      items: [{ productId: prod.id, quantity: qty }],
      notes: `Automated smart reorder recommendation for ${prod.sku}.`,
    });
  };

  // Reset state to default seed data
  const resetToDefaultData = () => {
    setProducts(INITIAL_PRODUCTS);
    setWarehouses(INITIAL_WAREHOUSES);
    setReceipts(INITIAL_RECEIPTS);
    setDeliveries(INITIAL_DELIVERIES);
    setTransfers(INITIAL_TRANSFERS);
    setAdjustments(INITIAL_ADJUSTMENTS);
    setStockLedger(INITIAL_LEDGER);
    setNotifications(INITIAL_NOTIFICATIONS);
    showToast('info', 'System Reset', 'Demo data reset to initial benchmark state.');
  };

  return (
    <InventoryContext.Provider
      value={{
        activeView,
        setActiveView,
        selectedWarehouseFilter,
        setSelectedWarehouseFilter,
        products,
        warehouses,
        receipts,
        deliveries,
        transfers,
        adjustments,
        stockLedger,
        notifications,
        toasts,
        currentUser,
        kpiStats,
        createProduct,
        updateProduct,
        createReceipt,
        validateReceipt,
        cancelReceipt,
        createDelivery,
        validateDelivery,
        cancelDelivery,
        createTransfer,
        validateTransfer,
        cancelTransfer,
        createAdjustment,
        createWarehouse,
        updateWarehouse,
        toggleWarehouseStatus,
        markNotificationRead,
        markAllNotificationsRead,
        showToast,
        removeToast,
        getSmartReorderSuggestions,
        quickReorderProduct,
        resetToDefaultData,
      }}
    >
      {children}
    </InventoryContext.Provider>
  );
};

export const useInventory = () => {
  const context = useContext(InventoryContext);
  if (!context) {
    throw new Error('useInventory must be used within an InventoryProvider');
  }
  return context;
};
