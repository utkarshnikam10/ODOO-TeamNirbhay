from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import math

from app.models.transfer import Transfer, TransferItem
from app.schemas.transfer import TransferCreate, TransferStatus
from app.schemas.pagination import PaginatedResponse
from app.repositories.transfer import transfer_repository
from app.repositories.product import product_repository
from app.repositories.warehouse import warehouse_repository
from app.repositories.location import location_repository
from app.services.stock import StockService

class TransferService:
    @staticmethod
    def create_transfer(db: Session, transfer_in: TransferCreate, user_id: int) -> Transfer:
        if transfer_repository.get_by_transfer_number(db, transfer_number=transfer_in.transfer_number):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer number already exists")
            
        if not warehouse_repository.get(db, id=transfer_in.source_warehouse_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid source_warehouse_id: {transfer_in.source_warehouse_id}")
        if not warehouse_repository.get(db, id=transfer_in.destination_warehouse_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid destination_warehouse_id: {transfer_in.destination_warehouse_id}")
            
        for item in transfer_in.items:
            if item.source_location_id == item.destination_location_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source and destination locations cannot be the same")
            if not product_repository.get(db, id=item.product_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid product_id: {item.product_id}")
            if not location_repository.get(db, id=item.source_location_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid source_location_id: {item.source_location_id}")
            if not location_repository.get(db, id=item.destination_location_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid destination_location_id: {item.destination_location_id}")

        transfer = Transfer(
            transfer_number=transfer_in.transfer_number,
            source_warehouse_id=transfer_in.source_warehouse_id,
            destination_warehouse_id=transfer_in.destination_warehouse_id,
            notes=transfer_in.notes,
            status=transfer_in.status.value,
            created_by_id=user_id
        )
        db.add(transfer)
        db.flush()
        
        for item in transfer_in.items:
            db_item = TransferItem(
                transfer_id=transfer.id,
                product_id=item.product_id,
                source_location_id=item.source_location_id,
                destination_location_id=item.destination_location_id,
                quantity=item.quantity
            )
            db.add(db_item)
            
        db.flush()
        return transfer

    @staticmethod
    def get_transfer(db: Session, transfer_id: int) -> Transfer:
        transfer = transfer_repository.get_with_items(db, id=transfer_id)
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
        return transfer

    @staticmethod
    def get_transfers(db: Session, page: int = 1, size: int = 50) -> PaginatedResponse:
        skip = (page - 1) * size
        items, total = transfer_repository.get_multi(db, skip=skip, limit=size)
        pages = math.ceil(total / size) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    def validate_transfer(db: Session, transfer_id: int) -> Transfer:
        transfer = TransferService.get_transfer(db, transfer_id)
        
        if transfer.status == TransferStatus.DONE.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer is already completed")
            
        if transfer.status == TransferStatus.CANCELED.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled transfer")
            
        for item in transfer.transfer_items:
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Invalid quantity {item.quantity} for product {item.product_id}"
                )
            
            # Use StockService.transfer_stock to perform the locked transfer safely
            StockService.transfer_stock(
                db=db,
                product_id=item.product_id,
                source_location_id=item.source_location_id,
                destination_location_id=item.destination_location_id,
                quantity=item.quantity,
                reference_id=transfer.id,
                reference_number=transfer.transfer_number,
                notes=f"Transfer Validation: {transfer.transfer_number}"
            )
            
        transfer.status = TransferStatus.DONE.value
        transfer.completed_at = datetime.now(timezone.utc)
        
        db.add(transfer)
        db.flush()
        
        return transfer

    @staticmethod
    def cancel_transfer(db: Session, transfer_id: int) -> Transfer:
        transfer = TransferService.get_transfer(db, transfer_id)
        
        if transfer.status == TransferStatus.DONE.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a completed transfer")
            
        transfer.status = TransferStatus.CANCELED.value
        db.add(transfer)
        db.flush()
        
        return transfer
