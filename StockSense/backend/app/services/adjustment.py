from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import math
from decimal import Decimal

from app.models.adjustment import Adjustment, AdjustmentItem
from app.schemas.adjustment import AdjustmentCreate, AdjustmentStatus
from app.schemas.pagination import PaginatedResponse
from app.repositories.adjustment import adjustment_repository
from app.repositories.product import product_repository
from app.repositories.location import location_repository
from app.services.stock import StockService

class AdjustmentService:
    @staticmethod
    def create_adjustment(db: Session, adjustment_in: AdjustmentCreate, user_id: int) -> Adjustment:
        if adjustment_repository.get_by_adjustment_number(db, adjustment_number=adjustment_in.adjustment_number):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Adjustment number already exists")
            
        for item in adjustment_in.items:
            if not product_repository.get(db, id=item.product_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid product_id: {item.product_id}")
            if not location_repository.get(db, id=item.location_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid location_id: {item.location_id}")

        adjustment = Adjustment(
            adjustment_number=adjustment_in.adjustment_number,
            reason=adjustment_in.reason,
            notes=adjustment_in.notes,
            status=adjustment_in.status.value,
            created_by_id=user_id
        )
        db.add(adjustment)
        db.flush()
        
        for item in adjustment_in.items:
            # Read current system quantity to calculate difference
            # Note: For accuracy during validation, this might change if stock changed in between,
            # but usually physical counts snapshot the difference.
            # We will calculate the difference at creation time. The requirements state:
            # 1. Read current system quantity. 3. Calculate difference. 6,7,8. Store old, counted, difference.
            current_stock = StockService.get_available_stock(db, item.product_id, item.location_id)
            difference = item.quantity_counted - current_stock
            
            db_item = AdjustmentItem(
                adjustment_id=adjustment.id,
                product_id=item.product_id,
                location_id=item.location_id,
                quantity_before=current_stock,
                quantity_counted=item.quantity_counted,
                difference=difference
            )
            db.add(db_item)
            
        db.flush()
        return adjustment

    @staticmethod
    def get_adjustment(db: Session, adjustment_id: int) -> Adjustment:
        adjustment = adjustment_repository.get_with_items(db, id=adjustment_id)
        if not adjustment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjustment not found")
        return adjustment

    @staticmethod
    def get_adjustments(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = adjustment_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def validate_adjustment(db: Session, adjustment_id: int) -> Adjustment:
        adjustment = AdjustmentService.get_adjustment(db, adjustment_id)
        
        if adjustment.status == AdjustmentStatus.DONE.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Adjustment is already completed")
            
        if adjustment.status == AdjustmentStatus.CANCELED.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled adjustment")
            
        for item in adjustment.adjustment_items:
            if item.difference != 0:
                # StockService.adjust_stock handles negative checks implicitly if new stock drops below 0.
                # However, our counted quantity is >= 0 so the adjustment won't make it negative unintentionally.
                StockService.adjust_stock(
                    db=db,
                    product_id=item.product_id,
                    location_id=item.location_id,
                    quantity_change=item.difference,
                    reference_id=adjustment.id,
                    reference_number=adjustment.adjustment_number,
                    notes=f"Adjustment Validation: {adjustment.adjustment_number} | Reason: {adjustment.reason}"
                )
            
        adjustment.status = AdjustmentStatus.DONE.value
        adjustment.applied_at = datetime.now(timezone.utc)
        
        db.add(adjustment)
        db.flush()
        
        return adjustment
