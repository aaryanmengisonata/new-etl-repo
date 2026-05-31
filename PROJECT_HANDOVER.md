# Project Handover & Runbook Documentation

This document provides a comprehensive handover of the **ETL Testing & Validation Framework** for development, operations, and QA teams.

---

## ⚡ Quick Start (Run Locally in Under 5 Minutes)

Run the following commands to get the entire application up and running locally:

### 1. Start the Backend
Open a terminal in the root directory:
```bash
cd new-etl-repo-main/backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python scripts/init_database.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Start the Frontend
Open a new terminal in the root directory:
```bash
cd new-etl-repo-main/Frontend/dashboard
npm install
npm run dev
```
The application will be accessible at:
* **Frontend Dashboard**: `http://localhost:5173`
* **FastAPI Swagger Docs**: `http://127.0.0.1:8000/docs`

---

## 1. Project Overview

### Project Name
*ETL Testing, Reconciliation & Validation Framework*

### Purpose and Business Objective
The framework serves as an automated validation and data reconciliation utility. It connects to various staging and production databases (PostgreSQL, SQLite, MS SQL Server, Snowflake, Microsoft Fabric) and APIs to perform:
1. **Reconciliation Auditing**: Column-by-column, row-by-row data comparisons (Integration Sentry).
2. **Dynamic Database Validations**: Automated checks for duplicate primary keys, null records, and value range metrics.
3. **Interactive Testing Workspace**: Real-time mock test suites (using PyTest in the background) with SSE-streamed test runs.

### High-Level Architecture
```
┌─────────────────┐       HTTP Requests       ┌────────────────┐
│  React (Vite)   │ ────────────────────────> │ FastAPI Router │
│    Frontend     │ <──────────────────────── │  (Uvicorn)     │
└─────────────────┘       SSE Log Streams     └────────────────┘
                                                │            │
                                                ▼            ▼
                                          ┌──────────┐  ┌──────────┐
                                          │  PyTest  │  │  SQLite  │
                                          │  Engine  │  │ (ORM DB) │
                                          └──────────┘  └──────────┘
```

### Tech Stack Used
* **Frontend**: React 18 SPA, Vite 6, TailwindCSS, Recharts (analytics charts), Lucide React (icons).
* **Backend**: Python 3.11, FastAPI (web frame), SQLAlchemy (ORM), Uvicorn (ASGI web server).
* **Database**: SQLite (default local db), PostgreSQL (dockerized configuration).
* **Testing Engines**: PyTest (test harness), Allure (execution reporting).

---

## 2. Prerequisites

Verify that the following tools are installed on the deployment host:
* **Python**: `3.8+` (Tested on `3.11.4` and `3.11.9`)
* **Node.js**: `18.0.0+` (Vite 6 requirements)
* **Package Manager**: npm (`9.0.0+`) or Yarn
* **Docker**: `20.10.0+` (If using the production PostgreSQL container setup)
* **ODBC Driver**: *Microsoft ODBC Driver 18 for SQL Server* (Mandatory to run Microsoft Fabric integration tests)

---

## 3. Environment Variables

Configure these variables inside the `backend/.env` file:

| Variable Name | Description | Required/Optional | Example Value |
|---|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string for the backend metrics database. | Required | `sqlite:///./etl_test_api.db` |
| `TEST_TIMEOUT` | Timeout limit (in seconds) for HTTP API calls. | Optional | `30` |

---

## 4. Backend Setup

### Backend Location
* **Path**: `new-etl-repo-main/backend/`

### Dependency Installation
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Database & Seed Initialization
```bash
python scripts/init_database.py
```
*(This automatically runs migrations and seeds SQLite with mock catalog data).*

### Running the App (Development)
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### PostgreSQL Docker Container Setup (Production Alternative)
To spin up a PostgreSQL instance instead of SQLite:
```bash
docker-compose up -d
python -c "from utils.etl_loader import ETLLoader; loader = ETLLoader(); loader.load_products_from_api()"
```

---

## 5. Frontend Setup

### Frontend Location
* **Path**: `new-etl-repo-main/Frontend/dashboard/`

### Installation & Run Commands
```bash
npm install
# Run Development Server
npm run dev
# Compile Production Bundle
npm run build
# Preview Compiled Build
npm run preview
```

---

## 6. Database Information

### Database Types Supported
* **SQLite (Local Dev)**: `etl_test_api.db` manages configuration and test run execution history.
* **PostgreSQL (Staging/Prod)**: Uses SQLAlchemy migrations and init scripts.
* **Inspect Engines**: Configured dynamically through the `/api/config/db` connection builder.

### Schema Overview (ORM Entities)
1. **`TestCaseDB` (`test_cases`)**: Holds definitions of all data-driven test cases (assertions, SQL statements, and active statuses).
2. **`ReportDB` (`reports`)**: Stores historical report outcomes, including status (`passed`/`failed`), timestamps, and JSON-serialized results.
3. **`PipelineAuditDB` (`pipeline_audits`)**: Manages the details of System Reconciler executions (logs, duration, variance details, and AI insights).

---

## 7. API Documentation

* **Base URL**: `http://127.0.0.1:8000`
* **Authentication**: None (Currently unauthenticated development sandbox).

### Major Endpoints

#### `POST /api/pipeline-auditor/test-connection`
* **Description**: Verifies database connection parameters.
* **Request Example**:
  ```json
  {
    "type": "database",
    "config": {
      "db_type": "sqlite",
      "db_name": "test_audit_src.db"
    }
  }
  ```
* **Response Example**:
  ```json
  {
    "status": "success",
    "message": "Connected successfully – 1 table found",
    "metadata": { "tables": ["products"] }
  }
  ```

#### `POST /api/pipeline-auditor/analyze`
* **Description**: Analyzes schema mapping differences.
* **Request Example**:
  ```json
  {
    "source_type": "database",
    "source_config": {"db_type": "sqlite", "db_name": "src.db"},
    "target_type": "database",
    "target_config": {"db_type": "sqlite", "db_name": "tgt.db"},
    "source_query": "SELECT * FROM products",
    "target_query": "SELECT * FROM products_silver",
    "key_columns": ["id"]
  }
  ```

#### `POST /api/integration-sentry/execute`
* **Description**: Compares data across systems and logs variances.
* **Response**: A detailed JSON detailing cell accuracy percentage and mismatched row keys.

---

## 8. Folder Structure

```
new-etl-repo-main/
│
├── backend/                              # Python Backend API & Testing Engine
│   ├── app/
│   │   ├── models/                       # ORM Definitions & Pydantic Configs
│   │   ├── routers/                      # Route Handlers (FastAPI)
│   │   └── services/                     # Business Logic (Reconciliation & Safety)
│   ├── config/                           # Configurations (master.properties)
│   ├── scripts/                          # DB Setup & Seeding scripts
│   ├── tests/                            # PyTest Harness (API, DB, Integration, ETL)
│   ├── utils/                            # Connection Clients (SQLite, PostgreSQL)
│   ├── docker-compose.yml                # Docker configurations
│   └── pytest.ini                        # PyTest setup parameters
│
└── Frontend/
    └── dashboard/                        # Vite React Client
        ├── src/
        │   ├── components/               # Shareable Layouts, Terminals, and Wizards
        │   ├── pages/                    # Views (Dashboard, Configuration, Sentry)
        │   ├── services/                 # API connection wrapper (api.js)
        │   └── main.jsx                  # Client entrypoint
        └── vite.config.js                # Build configs
```

---

## 9. Authentication & Authorization

* **Active Authentication**: **None**.
* **Security Matrix**:
  * FastAPI routes execute raw SQL queries based on UI input (monitored by the `validate_sql_safety` middleware).
  * *Next Steps Recommendation*: Before public staging deployment, implement OAuth2/JWT middleware blocks on all `/api/*` endpoints.

---

## 10. Deployment Guide

### Build Process
1. Run `npm run build` in the frontend path to generate production bundles in `/dist`.
2. Configure environment variables in `backend/.env`.

### Production Deployment Command
Run uvicorn behind a reverse proxy (like Nginx) in demonized state:
```bash
venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
```

---

## 11. Monitoring & Logging

* **Execution Logs**: SSE endpoint `/stream-logs/{engine}` captures subprocess test execution output.
* **Server Logs**: Uvicorn writes standard logs directly to stdout/stderr.
* **Health Check**: `/health` yields `{"status": "ok"}`.

---

## 12. Known Issues & Risks

1. **Microsoft Fabric Connection**: If the host machine does not have `ODBC Driver 18 for SQL Server` installed, Fabric test suites will fail.
2. **SSL Verification**: SSL certificate verification is disabled (`SSL_VERIFY = False` in `master.properties`) during mock calls to `fakestoreapi.com` to prevent environment setup issues. Ensure this is enabled in production configuration profiles.

---

## 13. Troubleshooting Guide

### Backend Not Starting
* **Cause**: virtual environment not activated, or `requirements.txt` packages not installed.
* **Solution**: Activate `venv` and run `pip install -r requirements.txt`. If SQLite file creation fails, verify file permissions for write access inside the backend folder.

### Database Connection Issues
* **Cause**: Database locked or files missing.
* **Solution**: Check if a local database file is locked by an active Python process. If using PostgreSQL, verify docker container status using `docker ps`.

---

## 14. Commands Cheat Sheet

### Frontend
```bash
npm install     # Install npm libraries
npm run dev     # Launch local development server
npm run build   # Build production assets
```

### Backend
```bash
python -m venv venv                # Create virtual environment
# Windows:
.\venv\Scripts\activate            # Activate virtual environment
# Unix:
source venv/bin/activate           # Activate virtual environment
pip install -r requirements.txt    # Install backend dependencies
python scripts/init_database.py    # Initialize local SQLite DB
python -m uvicorn app.main:app     # Launch dev server on port 8000
```

### Database (Postgres Docker)
```bash
docker-compose up -d    # Start database container
docker-compose down     # Stop database container
```

---

## 15. Code Quality Audit

We conducted a comprehensive codebase cleanup:
1. **Raw SQL Execution**: Blocked destructive commands using `validate_sql_safety` checks.
2. **Subprocess Thread Blocking**: Converted all backend pytest subprocess invocations to asynchronous (`asyncio.create_subprocess_exec`) to prevent API stalls.
3. **Python Binary Scoping**: Implemented `get_venv_python()` to prevent imports resolving outside the virtual environment.
4. **Pydantic Warnings**: Migrated config structures in `report.py` to Pydantic v2 `model_config`.
5. **Reconciliation Comparisons**: Swapped string conversions in `integration_sentry_service.py` for type-aware checks resolving floats, booleans, and null types.

---

## 16. Final Executive Summary

* **Project Status**: **Green / Complete**.
* **Completion Percentage**: `100%` of target remediation completed.
* **Working Modules**: Integration Sentry, API/ETL Pytest Suites, Schema Analyzer, Database Batch Validations, Configuration Management.
* **Blockers**: None.
* **Next Steps**: Implement OAuth2/JWT middleware authentication on the API layer, and install ODBC Driver 18 on staging servers to support Microsoft Fabric tests.
