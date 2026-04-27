-- ETL Test Database Setup
-- Run this in PostgreSQL

-- Create database
CREATE DATABASE etl_test;

-- Connect to etl_test database and run below:

-- Products table (matches API structure)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    image VARCHAR(500),
    rating_rate DECIMAL(3,2),
    rating_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETL log table for tracking data loads
CREATE TABLE etl_logs (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    records_processed INTEGER,
    records_success INTEGER,
    records_failed INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RUNNING'
);

-- Insert sample data for testing
INSERT INTO products (title, price, category, description) VALUES
('Test Product 1', 29.99, 'electronics', 'Sample product for testing'),
('Test Product 2', 49.99, 'clothing', 'Another test product');

-- Create indexes for performance
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_etl_logs_status ON etl_logs(status);