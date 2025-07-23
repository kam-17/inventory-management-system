-- Inventory Management System Database Schema
-- MySQL/MariaDB Compatible

-- Create database
-- CREATE DATABASE IF NOT EXISTS inventory_db;
-- USE inventory_db;

-- Users table with role-based access
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('SUPER_ADMIN', 'ADMIN', 'OFFICE', 'STORE', 'SERVICE_ENTRY') NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME NULL,
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME NULL
);

-- OTP logs for verification
CREATE TABLE IF NOT EXISTS otp_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    purpose VARCHAR(100) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    used_at DATETIME NULL,
    expires_at DATETIME NOT NULL,
    ip_address VARCHAR(45) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Audit logs for tracking all actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id INT NULL,
    old_values TEXT NULL,
    new_values TEXT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Site master data
CREATE TABLE IF NOT EXISTS site_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_code VARCHAR(20) UNIQUE NOT NULL,
    site_name VARCHAR(100) NOT NULL,
    client_name VARCHAR(100) NOT NULL,
    address TEXT NULL,
    contact_person VARCHAR(100) NULL,
    contact_phone VARCHAR(20) NULL,
    contact_email VARCHAR(100) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sub-sites under main sites
CREATE TABLE IF NOT EXISTS sub_sites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_id INT NOT NULL,
    sub_site_code VARCHAR(20) NOT NULL,
    sub_site_name VARCHAR(100) NOT NULL,
    address TEXT NULL,
    latitude FLOAT NULL,
    longitude FLOAT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES site_master(id) ON DELETE CASCADE,
    UNIQUE KEY unique_sub_site_code_per_site (site_id, sub_site_code)
);

-- Material categories
CREATE TABLE IF NOT EXISTS material_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_code VARCHAR(20) UNIQUE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Inventory materials master
CREATE TABLE IF NOT EXISTS inventory_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_code VARCHAR(50) UNIQUE NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    category_id INT NOT NULL,
    description TEXT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    hsn_code VARCHAR(20) NULL,
    gst_rate FLOAT DEFAULT 0.0,
    minimum_stock_level INT DEFAULT 0,
    maximum_stock_level INT NULL,
    unit_price FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES material_categories(id)
);

-- Current stock levels
CREATE TABLE IF NOT EXISTS inventory_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    current_quantity FLOAT DEFAULT 0.0,
    reserved_quantity FLOAT DEFAULT 0.0,
    available_quantity FLOAT DEFAULT 0.0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES inventory_materials(id) ON DELETE CASCADE,
    UNIQUE KEY unique_material_stock (material_id)
);

-- Inventory movements tracking
CREATE TABLE IF NOT EXISTS inventory_movement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    movement_type ENUM('INWARD', 'OUTWARD') NOT NULL,
    quantity FLOAT NOT NULL,
    unit_price FLOAT DEFAULT 0.0,
    total_value FLOAT DEFAULT 0.0,
    reference_type VARCHAR(50) NULL,
    reference_id INT NULL,
    reference_number VARCHAR(100) NULL,
    remarks TEXT NULL,
    supplier_name VARCHAR(200) NULL,
    invoice_number VARCHAR(100) NULL,
    invoice_date DATE NULL,
    gst_amount FLOAT DEFAULT 0.0,
    stock_before FLOAT NULL,
    stock_after FLOAT NULL,
    created_by INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES inventory_materials(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- DG Set letters (A, B, C, etc.)
CREATE TABLE IF NOT EXISTS dg_set_letters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    letter VARCHAR(5) UNIQUE NOT NULL,
    description VARCHAR(100) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- DG Set details and specifications
CREATE TABLE IF NOT EXISTS dg_set_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dg_set_number VARCHAR(50) UNIQUE NOT NULL,
    letter_id INT NOT NULL,
    make VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    rating_kva FLOAT NOT NULL,
    rating_kw FLOAT NOT NULL,
    frequency FLOAT DEFAULT 50.0,
    voltage VARCHAR(20) DEFAULT '415V',
    phase VARCHAR(20) DEFAULT '3-Phase',
    engine_make VARCHAR(100) NULL,
    engine_model VARCHAR(100) NULL,
    engine_serial_number VARCHAR(100) NULL,
    engine_capacity_cc INT NULL,
    engine_fuel_type VARCHAR(20) DEFAULT 'Diesel',
    alternator_make VARCHAR(100) NULL,
    alternator_model VARCHAR(100) NULL,
    alternator_serial_number VARCHAR(100) NULL,
    status ENUM('AVAILABLE', 'ASSIGNED', 'MAINTENANCE', 'TRANSFERRED', 'DECOMMISSIONED') DEFAULT 'AVAILABLE',
    current_site_id INT NULL,
    current_sub_site_id INT NULL,
    purchase_date DATE NULL,
    warranty_expiry DATE NULL,
    last_service_date DATE NULL,
    next_service_due DATE NULL,
    service_hours FLOAT DEFAULT 0.0,
    fuel_tank_capacity FLOAT NULL,
    weight_kg FLOAT NULL,
    dimensions VARCHAR(100) NULL,
    remarks TEXT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (letter_id) REFERENCES dg_set_letters(id),
    FOREIGN KEY (current_site_id) REFERENCES site_master(id),
    FOREIGN KEY (current_sub_site_id) REFERENCES sub_sites(id)
);

-- Service logs for DG sets
CREATE TABLE IF NOT EXISTS service_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dg_set_id INT NOT NULL,
    service_date DATE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    technician_name VARCHAR(100) NULL,
    service_company VARCHAR(100) NULL,
    hours_before_service FLOAT NULL,
    hours_after_service FLOAT NULL,
    work_description TEXT NULL,
    parts_replaced TEXT NULL,
    oil_changed BOOLEAN DEFAULT FALSE,
    filter_changed BOOLEAN DEFAULT FALSE,
    service_cost FLOAT DEFAULT 0.0,
    parts_cost FLOAT DEFAULT 0.0,
    total_cost FLOAT DEFAULT 0.0,
    next_service_hours FLOAT NULL,
    next_service_date DATE NULL,
    remarks TEXT NULL,
    service_pin VARCHAR(10) NULL,
    created_by INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (dg_set_id) REFERENCES dg_set_details(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Delivery Challan register
CREATE TABLE IF NOT EXISTS dg_dc_register (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dc_number VARCHAR(50) UNIQUE NOT NULL,
    dc_date DATE NOT NULL,
    status ENUM('DRAFT', 'DISPATCHED', 'PENDING_CLOSE', 'CLOSED', 'CANCELLED') DEFAULT 'DRAFT',
    site_id INT NOT NULL,
    sub_site_id INT NULL,
    vehicle_number VARCHAR(20) NULL,
    driver_name VARCHAR(100) NULL,
    driver_phone VARCHAR(20) NULL,
    transport_company VARCHAR(100) NULL,
    dc_type VARCHAR(50) DEFAULT 'DELIVERY',
    purpose VARCHAR(200) NULL,
    priority VARCHAR(20) DEFAULT 'NORMAL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dispatched_at DATETIME NULL,
    pending_close_at DATETIME NULL,
    closed_at DATETIME NULL,
    created_by INT NOT NULL,
    dispatched_by INT NULL,
    closed_by INT NULL,
    special_instructions TEXT NULL,
    remarks TEXT NULL,
    closure_remarks TEXT NULL,
    actual_delivery_date DATE NULL,
    received_by_name VARCHAR(100) NULL,
    received_by_designation VARCHAR(100) NULL,
    received_by_phone VARCHAR(20) NULL,
    pdf_generated BOOLEAN DEFAULT FALSE,
    pdf_path VARCHAR(255) NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES site_master(id),
    FOREIGN KEY (sub_site_id) REFERENCES sub_sites(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (dispatched_by) REFERENCES users(id),
    FOREIGN KEY (closed_by) REFERENCES users(id)
);

-- DC items (materials or DG sets)
CREATE TABLE IF NOT EXISTS dg_dc_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dc_id INT NOT NULL,
    material_id INT NULL,
    dg_set_id INT NULL,
    quantity FLOAT NOT NULL,
    unit_price FLOAT DEFAULT 0.0,
    total_value FLOAT DEFAULT 0.0,
    return_status ENUM('NOT_APPLICABLE', 'PENDING', 'PARTIAL', 'RETURNED') DEFAULT 'NOT_APPLICABLE',
    returnable BOOLEAN DEFAULT FALSE,
    expected_return_date DATE NULL,
    actual_return_date DATE NULL,
    returned_quantity FLOAT DEFAULT 0.0,
    description TEXT NULL,
    serial_numbers TEXT NULL,
    remarks TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (dc_id) REFERENCES dg_dc_register(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES inventory_materials(id),
    FOREIGN KEY (dg_set_id) REFERENCES dg_set_details(id),
    CONSTRAINT check_item_type CHECK (
        (material_id IS NOT NULL AND dg_set_id IS NULL) OR 
        (material_id IS NULL AND dg_set_id IS NOT NULL)
    )
);

-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_otp_logs_user_purpose ON otp_logs(user_id, purpose);
CREATE INDEX idx_audit_logs_user_table ON audit_logs(user_id, table_name);
CREATE INDEX idx_inventory_movement_material ON inventory_movement(material_id);
CREATE INDEX idx_inventory_movement_type_date ON inventory_movement(movement_type, created_at);
CREATE INDEX idx_service_logs_dg_set ON service_logs(dg_set_id);
CREATE INDEX idx_service_logs_date ON service_logs(service_date);
CREATE INDEX idx_dc_register_status ON dg_dc_register(status);
CREATE INDEX idx_dc_register_site ON dg_dc_register(site_id);
CREATE INDEX idx_dc_register_created_by ON dg_dc_register(created_by);
CREATE INDEX idx_dc_items_dc ON dg_dc_items(dc_id);
CREATE INDEX idx_materials_category ON inventory_materials(category_id);
CREATE INDEX idx_materials_code ON inventory_materials(material_code);
CREATE INDEX idx_dgsets_site ON dg_set_details(current_site_id);
CREATE INDEX idx_dgsets_status ON dg_set_details(status);