# StockSense — Core Inventory & Business Logic Architecture

**Project:** StockSense — Odoo × LPU Jalandhar Hackathon 2026  
**Team:** Team Nirbhay  
**Module Author:** Utkarsh (Inventory Intelligence + Core Business Logic)  

---

## 1. Overview & Architecture Boundary

The StockSense backend implements a layered, transactional architecture designed for production inventory operations:

```
FastAPI REST API Routes (Routers)
              ↓
  Service / Business Logic Layer (Utkarsh's Module)
  ├── stock_service.py
  ├── receipt_service.py
  ├── delivery_service.py
  ├── transfer_service.py
  ├── adjustment_service.py
  └── ledger_service.py
              ↓
 SQLAlchemy 2.0 ORM / Mapped Models (PostgreSQL 16)
```

### Architectural Principles:
1. **Separation of Concerns:** Route handlers perform HTTP parsing and authentication; all business rules, quantity invariants, and stock updates reside strictly in the service layer.
2. **Atomic Consistency:** Every stock-mutating transaction is wrapped in a transactional scope (`BEGIN ... COMMIT`). If validation fails at any point, the entire operation is rolled back, preventing partial stock state.
3. **No Phantom / Negative Stock:** Stock quantities cannot drop below zero. Deliveries and transfers pre-validate on-hand inventory across all line items before executing any mutations.
4. **Append-Only Auditing:** Every movement generates an immutable `StockLedger` audit record capturing the product, location, quantity change, balance after, reference transaction, and user ID.

---

## 2. Stock Calculation Engine (`stock_service.py`)

The `StockService` manages `Stock` records keyed by `(product_id, location_id)` with a unique constraint.

### Key Operations:
- **`get_available_quantity(product_id, location_id) -> Decimal`**: Returns physical on-hand quantity or `Decimal('0.000')` if no record exists.
- **`get_total_stock_for_product(product_id) -> Decimal`**: Aggregates company-wide stock across all warehouse locations for invariant checks.
- **`increase_stock(product_id, location_id, quantity) -> Stock`**: Adds `quantity` (validated positive) and updates `quantity`.
- **`decrease_stock(product_id, location_id, quantity) -> Stock`**: Validates `available >= quantity`. Throws `InsufficientStockError` if stock would become negative.
- **`move_stock(product_id, source_location_id, dest_location_id, quantity) -> (Stock, Stock)`**: Atomically decreases the source location and increases the destination location within the same database transaction.
- **`apply_adjustment(product_id, location_id, physical_qty) -> (before, physical, diff, stock)`**: Computes difference $D = Q_{\text{physical}} - Q_{\text{before}}$ and updates stock quantity to the verified physical count.

---

## 3. Goods Receipt Workflow (`receipt_service.py`)

A receipt represents incoming stock from suppliers or purchase orders.

### Execution Lifecycle:
1. **Lookup & Existence Check:** Fetch `Receipt` by primary key. Raise `ReceiptNotFoundError` if missing.
2. **State Validation:** Ensure `receipt.status == 'draft'`. If already validated or completed, reject with `DuplicateValidationError` or `InvalidTransactionStateError`.
3. **Empty Check & Item Validation:** Verify receipt has at least one line item. For each item:
   - Validate quantity $Q > 0$ (`validate_positive_quantity`).
   - Validate product and location existence.
4. **Stock Mutation:** Call `stock_service.increase_stock(product_id, location_id, qty)`.
5. **Ledger Writing:** Create `RECEIPT` ledger entry with $+Q$, recorded balance before, and balance after.
6. **State Transition:** Set `receipt.status = 'validated'`, timestamp `received_at`, and commit atomically.

---

## 4. Customer Delivery Workflow (`delivery_service.py`)

A delivery represents outgoing goods for customer sales orders.

### Strict Pre-Check Guarantee (All-or-Nothing):
1. **Fetch & State Validation:** Fetch `Delivery`, ensure `status == 'draft'`.
2. **Item Validation:** Ensure line items exist and each requested quantity $Q_{\text{ordered}} > 0$.
3. **Comprehensive Pre-Check Phase:** Before mutating **any** item's stock, iterate through all line items and check:
   $$Q_{\text{available}} \ge Q_{\text{ordered}}$$
   If **any** line item fails, immediately raise `InsufficientStockError`. No stock is modified.
4. **Stock Decrement Phase:** Once all items are verified available, decrement stock using `stock_service.decrease_stock`.
5. **Ledger Auditing:** Create `DELIVERY` ledger entry with $-Q$ and updated balance.
6. **State Transition:** Update `delivery.status = 'validated'` and commit.

---

## 5. Internal Transfer Workflow (`transfer_service.py`)

Transfers shift goods between bins or warehouses while maintaining company inventory invariants.

### Fundamental Invariant:
$$\sum_{\text{locations}} \text{Stock}_{\text{after}} = \sum_{\text{locations}} \text{Stock}_{\text{before}}$$

### Validation Flow:
1. **Location Distinctness:** Ensure `source_location_id != destination_location_id`. Transfers to the same location are rejected with `SameLocationTransferError`.
2. **Sufficient Source Stock:** Pre-check that source location has sufficient quantity for all items.
3. **Atomic Shift:** For each item:
   - Source location: $-Q$
   - Destination location: $+Q$
4. **Dual Ledger Posting:**
   - Source: `TRANSFER_OUT` with $-Q$
   - Destination: `TRANSFER_IN` with $+Q$
5. **Commit:** Persist changes atomically.

---

## 6. Physical Inventory Adjustment Workflow (`adjustment_service.py`)

Reconciles recorded database stock against physical inventory counts (cycle counts).

### Traceability Rules:
1. Physical count must be non-negative: $Q_{\text{physical}} \ge 0$.
2. Discrepancy is explicitly calculated:
   $$\Delta = Q_{\text{physical}} - Q_{\text{recorded}}$$
3. Stock is updated directly to $Q_{\text{physical}}$.
4. Line item preserves `quantity_before`, `quantity_after`, and `difference` for managerial audit.
5. Ledger entry is created with operation `ADJUSTMENT`, recording $\Delta$, reason string, and validating user ID.

---

## 7. Append-Only Stock Ledger (`ledger_service.py`)

The canonical, immutable audit log of the enterprise.

### Schema Fields:
- `product_id` (FK to products)
- `location_id` (FK to locations)
- `operation_type` (`RECEIPT`, `DELIVERY`, `TRANSFER_IN`, `TRANSFER_OUT`, `ADJUSTMENT`, `OPENING_STOCK`)
- `quantity_change` (Decimal, signed: positive for additions, negative for deductions)
- `balance_after` (Decimal, on-hand balance immediately following the change)
- `reference_id` / `reference_number` (Link to parent business document)
- `created_at` (UTC timestamp)
- `notes` (Contextual remarks)
