from fastapi import APIRouter

from app.routers import auth, health, category, product, warehouse, location, receipt, delivery, transfer, adjustment, reorder_rule, stock, ledger, dashboard

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(category.router)
api_router.include_router(product.router)
api_router.include_router(warehouse.router)
api_router.include_router(location.router)
api_router.include_router(receipt.router)
api_router.include_router(delivery.router)
api_router.include_router(transfer.router)
api_router.include_router(adjustment.router)
api_router.include_router(reorder_rule.router)
api_router.include_router(stock.router)
api_router.include_router(ledger.router)
api_router.include_router(dashboard.router)
