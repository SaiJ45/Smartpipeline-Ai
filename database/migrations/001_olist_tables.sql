-- Olist E-Commerce Database Schema
-- Migration 001: Create core tables

-- olist_customers table
CREATE TABLE IF NOT EXISTS olist_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- olist_sellers table
CREATE TABLE IF NOT EXISTS olist_sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10),
    seller_city VARCHAR(100),
    seller_state VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- olist_products table
CREATE TABLE IF NOT EXISTS olist_products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100),
    product_name_length INT,
    product_description_length INT,
    product_photos_qty INT,
    product_weight_g FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- olist_geolocation table
CREATE TABLE IF NOT EXISTS olist_geolocation (
    geolocation_zip_code_prefix VARCHAR(10) NOT NULL,
    geolocation_lat FLOAT NOT NULL,
    geolocation_lng FLOAT NOT NULL,
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng)
);

-- olist_orders table
CREATE TABLE IF NOT EXISTS olist_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES olist_customers(customer_id) ON DELETE CASCADE,
    order_status VARCHAR(50),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    delivery_delay_days FLOAT GENERATED ALWAYS AS (
        CASE 
            WHEN order_delivered_customer_date IS NOT NULL AND order_estimated_delivery_date IS NOT NULL
            THEN EXTRACT(DAY FROM (order_delivered_customer_date - order_estimated_delivery_date))
            ELSE NULL
        END
    ) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- olist_order_items table
CREATE TABLE IF NOT EXISTS olist_order_items (
    order_id VARCHAR(50) NOT NULL REFERENCES olist_orders(order_id) ON DELETE CASCADE,
    order_item_id INT NOT NULL,
    product_id VARCHAR(50) NOT NULL REFERENCES olist_products(product_id) ON DELETE CASCADE,
    seller_id VARCHAR(50) NOT NULL REFERENCES olist_sellers(seller_id) ON DELETE CASCADE,
    price FLOAT,
    freight_value FLOAT,
    order_total_value FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, order_item_id)
);

-- olist_reviews table
CREATE TABLE IF NOT EXISTS olist_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL REFERENCES olist_orders(order_id) ON DELETE CASCADE,
    review_score INT CHECK (review_score >= 1 AND review_score <= 5),
    review_comment_title VARCHAR(100),
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- olist_payments table
CREATE TABLE IF NOT EXISTS olist_payments (
    order_id VARCHAR(50) NOT NULL REFERENCES olist_orders(order_id) ON DELETE CASCADE,
    payment_sequential INT NOT NULL,
    payment_type VARCHAR(50),
    payment_installments INT,
    payment_value FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, payment_sequential)
);

-- Indexes on Foreign Key columns
CREATE INDEX IF NOT EXISTS idx_olist_orders_customer_id ON olist_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_olist_order_items_product_id ON olist_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_olist_order_items_seller_id ON olist_order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_olist_order_items_order_id ON olist_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_olist_reviews_order_id ON olist_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_olist_payments_order_id ON olist_payments(order_id);

-- Indexes on Date columns
CREATE INDEX IF NOT EXISTS idx_olist_orders_order_purchase_timestamp ON olist_orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_olist_orders_order_approved_at ON olist_orders(order_approved_at);
CREATE INDEX IF NOT EXISTS idx_olist_orders_order_delivered_carrier_date ON olist_orders(order_delivered_carrier_date);
CREATE INDEX IF NOT EXISTS idx_olist_orders_order_delivered_customer_date ON olist_orders(order_delivered_customer_date);
CREATE INDEX IF NOT EXISTS idx_olist_orders_order_estimated_delivery_date ON olist_orders(order_estimated_delivery_date);
CREATE INDEX IF NOT EXISTS idx_olist_reviews_review_creation_date ON olist_reviews(review_creation_date);

-- Indexes on other frequently queried columns
CREATE INDEX IF NOT EXISTS idx_olist_orders_order_status ON olist_orders(order_status);
CREATE INDEX IF NOT EXISTS idx_olist_customers_customer_state ON olist_customers(customer_state);
CREATE INDEX IF NOT EXISTS idx_olist_sellers_seller_state ON olist_sellers(seller_state);
CREATE INDEX IF NOT EXISTS idx_olist_products_category ON olist_products(product_category_name_english);
CREATE INDEX IF NOT EXISTS idx_olist_reviews_review_score ON olist_reviews(review_score);
