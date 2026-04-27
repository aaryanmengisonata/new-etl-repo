import requests
import psycopg2
from datetime import datetime
import logging
from utils.db_client import DatabaseClient
from utils.api_client import APIClient

class ETLLoader:
    def __init__(self):
        self.db_client = DatabaseClient()
        self.api_client = APIClient()
        self.logger = logging.getLogger(__name__)
    
    def load_products_from_api(self):
        """Load products from API to database"""
        start_time = datetime.now()
        
        try:
            # Get products from API
            response = self.api_client.get("/products")
            products = response.json()
            
            # Log ETL start
            etl_log_id = self._log_etl_start("products_api", len(products))
            
            success_count = 0
            failed_count = 0
            
            for product in products:
                try:
                    # Insert/Update product
                    query = """
                    INSERT INTO products (id, title, price, description, category, image, rating_rate, rating_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        price = EXCLUDED.price,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        image = EXCLUDED.image,
                        rating_rate = EXCLUDED.rating_rate,
                        rating_count = EXCLUDED.rating_count,
                        updated_at = CURRENT_TIMESTAMP;
                    """
                    
                    rating = product.get('rating', {})
                    params = (
                        product['id'],
                        product['title'],
                        product['price'],
                        product.get('description'),
                        product['category'],
                        product.get('image'),
                        rating.get('rate'),
                        rating.get('count')
                    )
                    
                    self.db_client.execute_query(query, params)
                    success_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to insert product {product.get('id')}: {e}")
                    failed_count += 1
            
            # Log ETL completion
            self._log_etl_end(etl_log_id, success_count, failed_count)
            
            return success_count, failed_count
            
        except Exception as e:
            self.logger.error(f"ETL process failed: {e}")
            raise
    
    def _log_etl_start(self, source_name, total_records):
        """Log ETL process start"""
        query = """
        INSERT INTO etl_logs (source_name, records_processed, start_time, status)
        VALUES (%s, %s, %s, 'RUNNING')
        RETURNING id;
        """
        result = self.db_client.execute_query(query, (source_name, total_records, datetime.now()))
        return result[0][0] if result else None
    
    def _log_etl_end(self, etl_log_id, success_count, failed_count):
        """Log ETL process completion"""
        query = """
        UPDATE etl_logs 
        SET records_success = %s, records_failed = %s, end_time = %s, status = 'COMPLETED'
        WHERE id = %s;
        """
        self.db_client.execute_query(query, (success_count, failed_count, datetime.now(), etl_log_id))

if __name__ == "__main__":
    loader = ETLLoader()
    success, failed = loader.load_products_from_api()
    print(f"ETL completed: {success} success, {failed} failed")