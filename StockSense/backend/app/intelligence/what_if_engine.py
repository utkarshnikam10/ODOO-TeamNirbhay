"""
StockSense – What-If Inventory Simulator
==========================================
Simulates inventory scenarios IN MEMORY without touching production data.

CRITICAL SAFETY GUARANTEE:
    This module NEVER modifies the database.
    It performs all calculations on Python dataclass instances,
    NOT on SQLAlchemy ORM objects.
    Callers pass current state as parameters; this engine returns projections.

Supported scenarios
-------------------
A. Demand increase by X%
B. Supplier lead time increases by N days
C. Incoming shipment is delayed by N days
D. Expected delivery quantity increases by N units

Each scenario returns:
    - projected_stock        : float
    - projected_days_of_cover: float | None
    - projected_risk_level   : str
    - shortage_estimate      : float (0 if no shortage)
    - recommendation         : str
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.intelligence.risk_engine import RISK_THRESHOLDS, RISK_LEVEL_CRITICAL, RISK_LEVEL_HIGH, RISK_LEVEL_MEDIUM, RISK_LEVEL_LOW


@dataclass
class WhatIfInput:
    """Snapshot of current inventory state.  Comes from real DB data (via the caller)."""
    product_id: int
    product_name: str
    current_stock: float
    average_daily_demand: float         # units/day (computed from ledger)
    safety_stock: float
    incoming_stock: float               # from draft receipts
    supplier_lead_time_days: float
    reorder_point: Optional[float] = None


@dataclass
class WhatIfResult:
    """Simulation result – always in-memory, never persisted."""
    scenario_name: str
    scenario_description: str
    projected_stock: float
    projected_days_of_cover: Optional[float]  # None if demand=0
    projected_risk_level: str
    shortage_estimate: float                  # 0 if no shortage
    recommendation: str
    # Input echo for transparency
    inputs_used: dict


class WhatIfEngine:
    """Pure simulation engine – reads real data from caller, never writes to DB."""

    # ── IMPORTANT: No database session is stored. ──────────────────────────────
    # This class only accepts data through method parameters.
    # This design makes it impossible to accidentally write to the DB.

    def simulate_demand_increase(
        self,
        inputs: WhatIfInput,
        demand_increase_pct: float,
    ) -> WhatIfResult:
        """Scenario A: What if daily demand increases by demand_increase_pct%?

        Example:
            demand_increase_pct = 25.0  means demand goes up by 25%

        Args:
            inputs: Current real stock state (passed by caller from DB).
            demand_increase_pct: Percentage increase in demand (e.g. 25 for 25%).

        Returns:
            In-memory simulation result.
        """
        if demand_increase_pct < 0:
            raise ValueError("demand_increase_pct must be >= 0")

        new_demand = inputs.average_daily_demand * (1 + demand_increase_pct / 100)
        days_of_cover = self._days_of_cover(inputs.current_stock, new_demand)
        required = new_demand * inputs.supplier_lead_time_days + inputs.safety_stock
        shortage = max(0.0, required - inputs.current_stock - inputs.incoming_stock)
        risk = self._risk_level(days_of_cover)

        recommendation = (
            f"If demand for '{inputs.product_name}' increases by {demand_increase_pct:.0f}%, "
            f"daily usage rises to {new_demand:.2f} units/day. "
        )
        if shortage > 0:
            recommendation += (
                f"Current stock would be exhausted in approximately {days_of_cover:.1f} days "
                f"and a shortage of ~{shortage:.1f} units is projected. "
                f"Recommend ordering {shortage:.1f} additional units immediately."
            )
        else:
            recommendation += f"Stock is adequate at {days_of_cover:.1f} days of cover."

        return WhatIfResult(
            scenario_name="Demand Increase",
            scenario_description=f"Daily demand increased by {demand_increase_pct:.0f}%",
            projected_stock=inputs.current_stock,  # stock unchanged in this scenario
            projected_days_of_cover=days_of_cover,
            projected_risk_level=risk,
            shortage_estimate=round(shortage, 2),
            recommendation=recommendation,
            inputs_used={
                "original_daily_demand": inputs.average_daily_demand,
                "new_daily_demand": round(new_demand, 2),
                "demand_increase_pct": demand_increase_pct,
                "current_stock": inputs.current_stock,
            },
        )

    def simulate_lead_time_increase(
        self,
        inputs: WhatIfInput,
        extra_lead_time_days: float,
    ) -> WhatIfResult:
        """Scenario B: What if supplier lead time increases by N days?

        A longer lead time means we need more stock to cover the waiting period.

        Args:
            inputs: Current real stock state.
            extra_lead_time_days: Additional days added to lead time.

        Returns:
            In-memory simulation result.
        """
        if extra_lead_time_days < 0:
            raise ValueError("extra_lead_time_days must be >= 0")

        new_lead_time = inputs.supplier_lead_time_days + extra_lead_time_days
        required = inputs.average_daily_demand * new_lead_time + inputs.safety_stock
        shortage = max(0.0, required - inputs.current_stock - inputs.incoming_stock)
        days_of_cover = self._days_of_cover(inputs.current_stock, inputs.average_daily_demand)
        risk = self._risk_level(days_of_cover)

        recommendation = (
            f"If lead time for '{inputs.product_name}' increases by "
            f"{extra_lead_time_days:.0f} days (total={new_lead_time:.0f} days), "
        )
        if shortage > 0:
            recommendation += (
                f"an additional ~{shortage:.1f} units would be needed to maintain safety stock. "
                "Place a purchase order before the lead time increases."
            )
        else:
            recommendation += "current stock and incoming shipments are sufficient to cover the extended lead time."

        return WhatIfResult(
            scenario_name="Lead Time Increase",
            scenario_description=f"Lead time extended by {extra_lead_time_days:.0f} days",
            projected_stock=inputs.current_stock,
            projected_days_of_cover=days_of_cover,
            projected_risk_level=risk,
            shortage_estimate=round(shortage, 2),
            recommendation=recommendation,
            inputs_used={
                "original_lead_time_days": inputs.supplier_lead_time_days,
                "new_lead_time_days": new_lead_time,
                "extra_days": extra_lead_time_days,
                "required_stock": round(required, 2),
                "current_stock": inputs.current_stock,
                "incoming_stock": inputs.incoming_stock,
            },
        )

    def simulate_shipment_delay(
        self,
        inputs: WhatIfInput,
        delay_days: float,
    ) -> WhatIfResult:
        """Scenario C: What if the incoming shipment is delayed by N days?

        During the delay, demand continues consuming existing stock.
        incoming_stock is not available for 'delay_days' additional days.

        Args:
            inputs: Current real stock state.
            delay_days: Number of additional days before incoming stock arrives.

        Returns:
            In-memory simulation result.
        """
        if delay_days < 0:
            raise ValueError("delay_days must be >= 0")

        # Stock consumed during the delay period
        consumed_during_delay = inputs.average_daily_demand * delay_days
        projected_stock = max(0.0, inputs.current_stock - consumed_during_delay)
        shortage = max(0.0, consumed_during_delay - inputs.current_stock)
        days_of_cover = self._days_of_cover(projected_stock, inputs.average_daily_demand)
        risk = self._risk_level(days_of_cover)

        recommendation = (
            f"If the incoming shipment of '{inputs.product_name}' is delayed by "
            f"{delay_days:.0f} days, approximately {consumed_during_delay:.1f} units "
            "would be consumed from current stock. "
        )
        if shortage > 0:
            recommendation += (
                f"Stock would run out before the shipment arrives, causing a shortage of "
                f"~{shortage:.1f} units. Consider expediting the order or finding an alternative supplier."
            )
        else:
            recommendation += f"Projected stock at arrival time: {projected_stock:.1f} units ({days_of_cover:.1f} days cover)."

        return WhatIfResult(
            scenario_name="Shipment Delay",
            scenario_description=f"Incoming shipment delayed by {delay_days:.0f} days",
            projected_stock=round(projected_stock, 2),
            projected_days_of_cover=days_of_cover,
            projected_risk_level=risk,
            shortage_estimate=round(shortage, 2),
            recommendation=recommendation,
            inputs_used={
                "current_stock": inputs.current_stock,
                "incoming_stock": inputs.incoming_stock,
                "daily_demand": inputs.average_daily_demand,
                "delay_days": delay_days,
                "consumed_during_delay": round(consumed_during_delay, 2),
            },
        )

    def simulate_delivery_increase(
        self,
        inputs: WhatIfInput,
        extra_units: float,
    ) -> WhatIfResult:
        """Scenario D: What if an expected delivery brings extra_units more than planned?

        This is a positive scenario – more stock arriving than expected.

        Args:
            inputs: Current real stock state.
            extra_units: Additional units arriving on top of incoming_stock.

        Returns:
            In-memory simulation result.
        """
        if extra_units < 0:
            raise ValueError("extra_units must be >= 0")

        projected_stock = inputs.current_stock + inputs.incoming_stock + extra_units
        days_of_cover = self._days_of_cover(projected_stock, inputs.average_daily_demand)
        risk = self._risk_level(days_of_cover)

        recommendation = (
            f"If the incoming delivery for '{inputs.product_name}' brings {extra_units:.1f} "
            f"additional units, total projected stock would be {projected_stock:.1f} units "
            f"({days_of_cover:.1f} days of cover). "
            "Ensure storage capacity is sufficient before accepting oversized shipment."
        )

        return WhatIfResult(
            scenario_name="Delivery Quantity Increase",
            scenario_description=f"Delivery brings {extra_units:.1f} extra units",
            projected_stock=round(projected_stock, 2),
            projected_days_of_cover=days_of_cover,
            projected_risk_level=risk,
            shortage_estimate=0.0,
            recommendation=recommendation,
            inputs_used={
                "current_stock": inputs.current_stock,
                "original_incoming": inputs.incoming_stock,
                "extra_units": extra_units,
                "projected_stock": round(projected_stock, 2),
                "daily_demand": inputs.average_daily_demand,
            },
        )

    # ── Internal helpers (pure functions, no DB) ───────────────────────────────

    @staticmethod
    def _days_of_cover(stock: float, daily_demand: float) -> Optional[float]:
        if daily_demand == 0.0:
            return float("inf") if stock > 0 else 0.0
        return stock / daily_demand

    @staticmethod
    def _risk_level(days_of_cover: Optional[float]) -> str:
        if days_of_cover is None or days_of_cover == 0.0:
            return RISK_LEVEL_CRITICAL
        if days_of_cover == float("inf"):
            return RISK_LEVEL_LOW
        critical = RISK_THRESHOLDS["CRITICAL_DAYS"]
        high = RISK_THRESHOLDS["HIGH_DAYS"]
        medium = RISK_THRESHOLDS["MEDIUM_DAYS"]
        if days_of_cover < critical:
            return RISK_LEVEL_CRITICAL
        if days_of_cover < high:
            return RISK_LEVEL_HIGH
        if days_of_cover < medium:
            return RISK_LEVEL_MEDIUM
        return RISK_LEVEL_LOW
