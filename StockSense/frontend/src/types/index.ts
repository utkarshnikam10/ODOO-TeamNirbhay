export type ViewType =
  | 'dashboard'
  | 'products'
  | 'receipts'
  | 'deliveries'
  | 'transfers'
  | 'adjustments'
  | 'ledger'
  | 'warehouses'
  | 'profile';

export type StockStatus = 'In Stock' | 'Low Stock' | 'Out of Stock';

export interface Product {
  id: string;
  name: string;
  sku: string;
  category: string;
  unit: string;
  minReorderLevel: number;
  warehouseStock: Record<string, number>; // warehouseId -> stock
  description: string;
  createdAt: string;
}

export interface Warehouse {
  id: string;
  code: string;
  name: string;
  location: string;
  address: string;
  status: 'Active' | 'Inactive';
}

export type DocumentStatus = 'Draft' | 'Waiting' | 'Ready' | 'Done' | 'Canceled';

export interface ReceiptItem {
  productId: string;
  quantity: number;
  unitPrice?: number;
}

export interface Receipt {
  id: string;
  receiptNo: string;
  supplier: string;
  date: string;
  destinationWarehouseId: string;
  items: ReceiptItem[];
  status: DocumentStatus;
  notes?: string;
  createdBy: string;
}

export interface DeliveryItem {
  productId: string;
  quantity: number;
}

export interface DeliveryOrder {
  id: string;
  deliveryNo: string;
  customer: string;
  date: string;
  sourceWarehouseId: string;
  items: DeliveryItem[];
  status: DocumentStatus;
  notes?: string;
  createdBy: string;
}

export interface TransferItem {
  productId: string;
  quantity: number;
}

export interface InternalTransfer {
  id: string;
  transferNo: string;
  date: string;
  sourceWarehouseId: string;
  destinationWarehouseId: string;
  items: TransferItem[];
  reason: string;
  status: 'Draft' | 'Ready' | 'Done' | 'Canceled';
  createdBy: string;
}

export interface InventoryAdjustment {
  id: string;
  adjustmentNo: string;
  date: string;
  warehouseId: string;
  productId: string;
  systemQuantity: number;
  physicalQuantity: number;
  difference: number;
  reason: string;
  notes?: string;
  status: 'Draft' | 'Completed' | 'Canceled';
  createdBy: string;
}

export type LedgerMovementType = 'Receipt' | 'Delivery' | 'Transfer' | 'Adjustment';

export interface StockLedgerEntry {
  id: string;
  timestamp: string;
  referenceNo: string;
  type: LedgerMovementType;
  productId: string;
  productName: string;
  sku: string;
  warehouseId: string;
  warehouseName: string;
  fromLocation: string;
  toLocation: string;
  quantity: number;
  beforeStock: number;
  afterStock: number;
  performedBy: string;
  status: string;
}

export interface AppNotification {
  id: string;
  type: 'low_stock' | 'receipt' | 'delivery' | 'transfer' | 'adjustment';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  linkView?: ViewType;
  linkId?: string;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar: string;
  lastLogin: string;
}

export interface SmartReorderSuggestion {
  product: Product;
  currentStock: number;
  reorderLevel: number;
  suggestedQty: number;
  reason: string;
  primaryWarehouseId: string;
  primaryWarehouseName: string;
}
