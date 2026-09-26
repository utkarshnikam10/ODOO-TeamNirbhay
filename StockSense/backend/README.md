# StockSense Inventory Management System Backend

StockSense is a comprehensive, production-grade Inventory Management System backend designed for high-performance and absolute transactional safety. Built with FastAPI and PostgreSQL, it provides robust capabilities for multi-warehouse tracking, dynamic stock ledger auditing, role-based access control, and complex inventory mutations (receipts, deliveries, transfers, and adjustments).

This repository contains the backend component, fully configured for immediate execution and hackathon demonstration.

---

## 🏗 Architecture

The backend implements a highly scalable **Layered Architecture (N-Tier)**:

- **Routers (`app/routers/`)**: Handles FastAPI HTTP request ingestion, route definition, payload validation, and Dependency Injection.
- **Services (`app/services/`)**: The core brain. Encapsulates all cross-domain business logic, ensuring strict ACID properties and data validity prior to database mutation.
- **Repositories (`app/repositories/`)**: Abstracted data access layers wrapping SQLAlchemy ORM calls. Ensures efficient execution (`ILIKE` searches, native pagination via `OFFSET/LIMIT`) without loading unnecessary memory payload.
- **Models (`app/models/`)**: Declarative SQLAlchemy PostgreSQL table schemas.
- **Schemas (`app/schemas/`)**: Strict Pydantic models serving as API contracts for Request/Response validation and Swagger generation.

### Important Design Decisions
1. **Strictly Auditable Ledger**: Every stock mutation natively generates an immutable record in the `StockLedger`. The system is built around the fundamental rule that stock can never magically change—it must traverse through a standardized Operation (Receipt, Delivery, Transfer, Adjustment).
2. **ACID Transaction Safety & Deadlock Prevention**: The `StockService` handles concurrent modifications explicitly via Row-Level Locking (`with_for_update()`). Bi-directional multi-location transfers deterministically lock lower `location_id`s first to inherently defeat race-condition deadlocks.
3. **Database-first Filtering**: List endpoints utilize native SQL `WHERE` clauses for search filtering and pagination, avoiding excessive Python footprint.

---

## 🗄 Database Structure

The PostgreSQL schema relies on tightly coupled foreign key constraints and atomic structures:
- `users`: Role-based authentication (Admin, Manager, Staff).
- `categories`, `products`: Core items with unique `SKU`s and barcode capabilities.
- `warehouses`, `locations`: Multi-tiered structural mapping. Products are bound to specific locations.
- `stock`: Current physical quantity tracking by `(product_id, location_id)`.
- `receipts`, `deliveries`, `transfers`, `adjustments`: Transactional operations governing flow logic.
- `stock_ledger`: Immutable chronological audit log binding directly back to the triggering transaction.
- `reorder_rules`: Threshold definitions governing dynamic Dashboard logic for `Low Stock` evaluation.

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 15+

### Installation
1. Navigate to the backend directory and activate your virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
Create your environment variables natively by duplicating the template:
```bash
cp .env.example .env
```
Ensure your `DATABASE_URL` matches your local active PostgreSQL installation.

---

## 🛠 PostgreSQL Configuration & Migrations

StockSense uses Alembic to manage database schema migrations cleanly. Ensure your target PostgreSQL database (e.g. `stocksense_db`) is created beforehand.

Run the latest database schema migrations to synchronize your Postgres instance:
```bash
alembic upgrade head
```

*(For developers: To generate a new migration after modifying `app/models/`)*
```bash
alembic revision --autogenerate -m "description of changes"
```

---

## 🏃 Running the Server

Start the high-performance Uvicorn ASGI web server (includes hot-reloading for development):
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Running Tests

The backend suite features **55 strictly evaluated integration tests** enforcing edge cases and locking strategies. Testing utilizes an isolated transactional rollback strategy to maintain total idempotency natively via `pytest`.

```bash
pytest
```
*Note: The test suite actively spins up dependent database operations and executes via the FastAPI TestClient.*

---

## 📖 API Documentation

FastAPI natively outputs fully interactive, OpenAPI compliant Swagger documentation. 

Once the server is running, navigate to:
- **Swagger UI (Interactive):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc (Static Documentation):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

Ensure you authorize via the Swagger UI using a valid JWT bearer token (acquired via `/api/v1/auth/login`) before testing protected `/api/v1/` routes.

---

## 📦 Stock Flow (Summary)

1. **Drafting**: Create a `Receipt` (Incoming) or `Delivery` (Outgoing). This creates the document but *does not* mutate inventory.
2. **Validation**: Submitting the `/validate` endpoint checks the inventory rules (e.g., prevents negative stock on outbound deliveries).
3. **Execution**: If valid, the system wraps the mutation in an atomic transaction, updates physical `Stock`, generates a historical `StockLedger` snapshot, and marks the document as `DONE`.
