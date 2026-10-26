CREATE DATABASE IF NOT EXISTS banking_analysis;
USE banking_analysis;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_type ENUM('SAVINGS','CURRENT','STUDENT') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_accounts_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type ENUM('DEPOSIT','WITHDRAWAL') NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    description VARCHAR(200) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_account FOREIGN KEY (account_id)
        REFERENCES accounts(account_id) ON DELETE RESTRICT,
    CONSTRAINT chk_positive_amount CHECK (amount > 0),
    INDEX idx_transactions_date (transaction_date),
    INDEX idx_transactions_account (account_id)
);
