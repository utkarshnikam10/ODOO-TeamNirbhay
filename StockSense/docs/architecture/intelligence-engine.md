# StockSense — Inventory Intelligence Engine Architecture

**Project:** StockSense — Odoo × LPU Jalandhar Hackathon 2026  
**Team:** Team Nirbhay  
**Module Author:** Utkarsh (Inventory Intelligence + Core Business Logic)  

---

## 1. Design Philosophy: Explainable Intelligence

StockSense deliberately rejects opaque "black-box" machine learning, arbitrary AI scores, or external LLM API dependencies for core inventory math. In enterprise supply chains, every stockout warning, purchase recommendation, and anomaly alert must be:
1. **Auditable:** Backed by real ledger records and verifiable formulas.
2. **Transparent:** Accompanied by a deterministic, human-readable reason string.
3. **Safe:** Never capable of mutating production database records during scenario simulations.

---

## 2. Stock Risk Engine (`risk_engine.py`)

Assesses stockout vulnerability and assigns explainable risk ratings for every SKU.

### Formulas & Math:
1. **Average Daily Usage ($ADU$):**
   Derived from actual `DELIVERY` records in `StockLedger` over a trailing $N$-day window (default 30 days):
   $$ADU = \frac{\sum_{t \in \text{window}} |\Delta Q_{\text{delivery}}|}{N}$$
2. **Days of Cover ($DoC$):**
   $$DoC = \begin{cases} \infty & \text{if } ADU = 0 \text{ and } Q_{\text{stock}} > 0 \\ 0 & \text{if } ADU = 0 \text{ and } Q_{\text{stock}} = 0 \\ \frac{Q_{\text{stock}}}{ADU} & \text{otherwise} \end{cases}$$

### Centralized Configurable Thresholds:
| Risk Level | Threshold Criterion | Business Action |
|---|---|---|
| **CRITICAL** | $DoC < 2.0$ days or $Q_{\text{stock}} = 0$ | Immediate emergency reorder / expedited shipment. |
| **HIGH** | $2.0 \le DoC < 7.0$ days | Expedite purchase order before stock drops to zero. |
| **MEDIUM** | $7.0 \le DoC < 14.0$ days | Schedule upcoming replenishment with standard lead time. |
| **LOW** | $DoC \ge 14.0$ days | Stock healthy; no immediate intervention needed. |

### Output Example:
```json
{
  "product_id": 101,
  "product_name": "Industrial Widget A",
  "risk_level": "HIGH",
  "days_of_cover": 4.5,
  "current_stock": 45.0,
  "average_daily_usage": 10.0,
  "reason": "'Industrial Widget A' has only 4.5 days of cover (current stock: 45.0, average usage: 10.0/day). High risk threshold is 7 days."
}
```

---

## 3. Reorder Recommendation Engine (`reorder_engine.py`)

Calculates exact, explainable replenishment quantities to optimize working capital while preventing stockouts.

### Formula & Mathematical Derivation:
$$\text{Demand During Lead Time} = ADU \times L_{\text{days}}$$
$$\text{Required Stock} = \text{Demand During Lead Time} + \text{Safety Stock}$$
$$\text{Recommended Order Quantity} = \max\left(0, \text{Required Stock} - Q_{\text{current}} - Q_{\text{incoming}}\right)$$

Where:
- $ADU$: Average daily demand from delivery history.
- $L_{\text{days}}$: Supplier lead time in days (from `ReorderRule`).
- $\text{Safety Stock}$: Buffer inventory to absorb demand spikes (from `ReorderRule.min_quantity`).
- $Q_{\text{current}}$: On-hand available stock.
- $Q_{\text{incoming}}$: Quantity on draft purchase receipts not yet validated.

### Explainable Reasoning:
If recommended order $> 0$, the engine reports the exact arithmetic shortfall:
> *"Industrial Widget A should be reordered. Formula: demand_during_lead_time (10.0/day x 5 days = 50.0) + safety_stock (20.0) = required_stock (70.0). Current stock (45.0) + incoming (0.0) = 45.0, which is short by 25.0 units."*

---

## 4. Anomaly Detection Engine (`anomaly_engine.py`)

Identifies fraudulent transactions, shrinkage, data entry errors, or unexpected spikes in stock movements using statistical and rule-based detectors.

### Active Detection Rules:
1. **Statistical Outlier in Physical Adjustments ($Z$-Score):**
   Calculates sample mean $\mu$ and standard deviation $\sigma$ of adjustment magnitudes for each product over a 30-day window (minimum 5 samples required):
   $$Z = \frac{|\Delta Q| - \mu}{\sigma}$$
   Flagged if $Z > 2.0$ (statistically outside 95% confidence bounds).
2. **Repeated Adjustments Spike:**
   Flags any SKU with $> 3$ physical count adjustments within a rolling 7-day period (indicates systematic inventory leakage or poor counting practices).
3. **Large Delivery Outlier:**
   Flags outgoing customer dispatches that exceed recent average sales deliveries by $> 2.0\sigma$.
4. **High Frequency Velocity:**
   Detects SKUs undergoing $> 10$ inventory transactions within a 24-hour window.

### Structure of an Anomaly Alert:
```json
{
  "product_id": 101,
  "event_type": "LARGE_ADJUSTMENT",
  "severity": "CRITICAL",
  "reason": "Adjustment of +150.0 units for 'Industrial Widget A' is 2.8 standard deviations above the recent mean adjustment magnitude (23.1 units, std_dev=45.2). This is statistically unusual.",
  "supporting_values": {
    "quantity_change": 150.0,
    "z_score": 2.8,
    "threshold_z": 2.0
  }
}
```

---

## 5. What-If Inventory Simulator (`what_if_engine.py`)

A pure in-memory projection engine for managerial decision-making and stress-testing.

### Safety Guarantee:
`WhatIfEngine` **never accepts a database connection or session**. It operates strictly on immutable in-memory data structures (`WhatIfInput`), returning `WhatIfResult`. It is mathematically and architecturally impossible for a simulation to mutate live production inventory.

### Supported Simulations:
1. **Demand Surge:**
   Simulates demand increasing by $+X\%$ (e.g., $+25\%$).
   $$ADU_{\text{sim}} = ADU \times (1 + X/100)$$
   Computes revised Days of Cover, anticipated stockout date, and inventory shortage.
2. **Supplier Lead Time Delays:**
   Simulates supply chain disruptions where supplier lead time increases by $+N$ days.
   Evaluates whether existing safety stock covers the extended lead time window.
3. **Incoming Shipment Delays:**
   Evaluates inventory vulnerability if pending supplier orders arrive $N$ days late.
4. **Delivery Demand Surge:**
   Simulates immediate bulk order dispatch of $+N$ units.
