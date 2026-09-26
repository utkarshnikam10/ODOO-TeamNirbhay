from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import math

from app.models.delivery import Delivery, DeliveryItem
from app.schemas.delivery import DeliveryCreate, DeliveryStatus
from app.schemas.pagination import PaginatedResponse
from app.repositories.delivery import delivery_repository
from app.repositories.product import product_repository
from app.repositories.location import location_repository
from app.services.stock import StockService

class DeliveryService:
    @staticmethod
    def create_delivery(db: Session, delivery_in: DeliveryCreate, user_id: int) -> Delivery:
        if delivery_repository.get_by_delivery_number(db, delivery_number=delivery_in.delivery_number):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery number already exists")
            
        for item in delivery_in.items:
            if not product_repository.get(db, id=item.product_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid product_id: {item.product_id}")
            if not location_repository.get(db, id=item.location_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid location_id: {item.location_id}")

        delivery = Delivery(
            delivery_number=delivery_in.delivery_number,
            customer_name=delivery_in.customer_name,
            notes=delivery_in.notes,
            status=delivery_in.status.value,
            created_by_id=user_id
        )
        db.add(delivery)
        db.flush()
        
        for item in delivery_in.items:
            db_item = DeliveryItem(
                delivery_id=delivery.id,
                product_id=item.product_id,
                location_id=item.location_id,
                quantity_ordered=item.quantity_ordered,
                unit_price=item.unit_price
            )
            db.add(db_item)
            
        db.flush()
        return delivery

    @staticmethod
    def get_delivery(db: Session, delivery_id: int) -> Delivery:
        delivery = delivery_repository.get_with_items(db, id=delivery_id)
        if not delivery:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
        return delivery

    @staticmethod
    def get_deliveries(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = delivery_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def validate_delivery(db: Session, delivery_id: int) -> Delivery:
        delivery = DeliveryService.get_delivery(db, delivery_id)
        
        if delivery.status == DeliveryStatus.DONE.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery is already completed")
            
        if delivery.status == DeliveryStatus.CANCELED.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled delivery")
            
        for item in delivery.delivery_items:
            if item.quantity_ordered <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Invalid quantity {item.quantity_ordered} for product {item.product_id}"
                )
            
            # Check available stock before validation (although issue_stock checks it too, this is requested explicitly)
            available = StockService.get_available_stock(db, item.product_id, item.location_id)
            if available < item.quantity_ordered:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Insufficient stock for product {item.product_id}. Available: {available}, Required: {item.quantity_ordered}"
                )
            
            # Issue stock
            StockService.issue_stock(
                db=db,
                product_id=item.product_id,
                location_id=item.location_id,
                quantity=item.quantity_ordered,
                reference_id=delivery.id,
                reference_number=delivery.delivery_number,
                notes=f"Delivery Validation: {delivery.delivery_number}"
            )
            item.quantity_delivered = item.quantity_ordered
            
        delivery.status = DeliveryStatus.DONE.value
        delivery.shipped_at = datetime.now(timezone.utc)
        
        db.add(delivery)
        db.flush()
        
        return delivery

    @staticmethod
    def cancel_delivery(db: Session, delivery_id: int) -> Delivery:
        delivery = DeliveryService.get_delivery(db, delivery_id)
        
        if delivery.status == DeliveryStatus.DONE.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a completed delivery")
            
        delivery.status = DeliveryStatus.CANCELED.value
        db.add(delivery)
        db.flush()
        
        return delivery
