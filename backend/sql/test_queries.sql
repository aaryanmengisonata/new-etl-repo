SELECT COUNT(*) FROM products WHERE category = 'accommodation';

SELECT COUNT(*) FROM products WHERE category = 'accommodation' AND (price <= 0 OR title IS NULL);

SELECT COUNT(*) FROM products WHERE category LIKE '%flight%' OR category LIKE '%travel%';

SELECT COUNT(*) FROM products WHERE category LIKE '%flight%' AND price > 500;

SELECT COUNT(*) FROM products WHERE price = (SELECT price FROM products WHERE id = 1);

SELECT COUNT(*) FROM products WHERE price < 1000;

SELECT COUNT(*) FROM products;

SELECT COUNT(*) FROM (SELECT id, COUNT(*) FROM products GROUP BY id HAVING COUNT(*) > 1);

SELECT COUNT(*) FROM products WHERE id IN (1,2,3,4,5);

SELECT COUNT(*) FROM products WHERE price > 0 AND title IS NOT NULL;

SELECT COUNT(DISTINCT category) FROM products;