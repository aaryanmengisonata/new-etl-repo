SELECT COUNT(*) FROM products;

SELECT COUNT(*) FROM products WHERE title IS NULL OR price IS NULL;

SELECT COUNT(*) FROM products WHERE category LIKE '%flight%' OR category LIKE '%travel%';

SELECT COUNT(*) FROM products WHERE category LIKE '%flight%' AND price > 500;

SELECT COUNT(*) FROM products WHERE id IN (1,2,3,4,5);

SELECT COUNT(*) FROM products WHERE price < 1000;

SELECT COUNT(*) FROM products WHERE id IN (SELECT id FROM products WHERE price > 0);

SELECT COUNT(DISTINCT category) FROM products WHERE price BETWEEN 10 AND 100;

SELECT COUNT(*) FROM products WHERE LENGTH(title) > 10;

SELECT COUNT(*) FROM products WHERE price != 0 AND category IS NOT NULL;

SELECT COUNT(*) FROM products WHERE created_at IS NOT NULL;

SELECT COUNT(*) FROM products WHERE rating_rate > 0;

SELECT 20 as api_count;

SELECT COUNT(*) FROM products WHERE price > 5;