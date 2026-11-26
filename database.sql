CREATE DATABASE IF NOT EXISTS inventory_management;
USE inventory_management;

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(80) NOT NULL,
    purchase_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    selling_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    quantity INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (quantity >= 0),
    CHECK (purchase_price >= 0),
    CHECK (selling_price >= 0),
    CHECK (reorder_level >= 0)
);

CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sales_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE RESTRICT,
    CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    movement_type ENUM('STOCK_IN', 'SALE', 'ADJUSTMENT') NOT NULL,
    quantity INT NOT NULL,
    note VARCHAR(255),
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movements_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE RESTRICT
);
