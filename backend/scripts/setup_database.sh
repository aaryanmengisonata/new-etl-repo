#!/bin/bash

echo "Setting up ETL Test Database..."

# Option 1: Using Docker (Recommended)
echo "Starting PostgreSQL with Docker..."
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Option 2: Manual PostgreSQL setup (if Docker not available)
# 1. Install PostgreSQL
# 2. Create database: createdb etl_test
# 3. Run: psql -d etl_test -f database_setup.sql

# Load initial data from API
echo "Loading data from API..."
python -c "from utils.etl_loader import ETLLoader; loader = ETLLoader(); loader.load_products_from_api()"

echo "Database setup complete!"
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: etl_test"
echo "  Username: postgres"
echo "  Password: password"