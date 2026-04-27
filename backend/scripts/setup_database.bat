@echo off
echo Setting up ETL Test Database...

echo Starting PostgreSQL with Docker...
docker-compose up -d

echo Waiting for database to be ready...
timeout /t 15 /nobreak

echo Loading data from API...
python -c "from utils.etl_loader import ETLLoader; loader = ETLLoader(); loader.load_products_from_api()"

echo Database setup complete!
echo Connection details:
echo   Host: localhost
echo   Port: 5432
echo   Database: etl_test
echo   Username: postgres
echo   Password: password

pause