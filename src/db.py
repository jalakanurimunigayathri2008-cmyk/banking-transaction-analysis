import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def get_connection():
    """Create a MySQL connection using local environment settings."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "banking_analysis"),
    )

def initialize_database():
    """Create the database tables. The database itself must already exist."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            display_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            account_type ENUM('SAVINGS','CURRENT','STUDENT') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_accounts_customer FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id) ON DELETE RESTRICT
        )
        """,
        """
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
        )
        """
    ]
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for statement in statements:
            cursor.execute(statement)
        conn.commit()
    finally:
        conn.close()

def seed_demo_data():
    """Insert deterministic, synthetic demo data only when the tables are empty."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] > 0:
            return

        customers = [("Aarav Demo",), ("Diya Sample",), ("Kiran Test",)]
        cursor.executemany("INSERT INTO customers (display_name) VALUES (%s)", customers)
        conn.commit()

        cursor.execute("SELECT customer_id FROM customers ORDER BY customer_id")
        customer_ids = [r[0] for r in cursor.fetchall()]
        account_rows = [
            (customer_ids[0], "SAVINGS"),
            (customer_ids[0], "STUDENT"),
            (customer_ids[1], "SAVINGS"),
            (customer_ids[2], "CURRENT"),
        ]
        cursor.executemany("INSERT INTO accounts (customer_id, account_type) VALUES (%s, %s)", account_rows)
        conn.commit()

        cursor.execute("SELECT account_id FROM accounts ORDER BY account_id")
        account_ids = [r[0] for r in cursor.fetchall()]
        transactions = [
            (account_ids[0], "2026-08-03", "DEPOSIT", 25000.00, "Synthetic salary"),
            (account_ids[0], "2026-08-05", "WITHDRAWAL", 3200.00, "Synthetic groceries"),
            (account_ids[0], "2026-09-01", "DEPOSIT", 25000.00, "Synthetic salary"),
            (account_ids[0], "2026-09-07", "WITHDRAWAL", 4200.00, "Synthetic bills"),
            (account_ids[1], "2026-09-10", "DEPOSIT", 1500.00, "Synthetic allowance"),
            (account_ids[1], "2026-09-12", "WITHDRAWAL", 300.00, "Synthetic books"),
            (account_ids[2], "2026-09-14", "DEPOSIT", 7000.00, "Synthetic transfer"),
            (account_ids[2], "2026-09-16", "WITHDRAWAL", 1200.00, "Synthetic shopping"),
            (account_ids[3], "2026-10-01", "DEPOSIT", 100000.00, "Synthetic business receipt"),
            (account_ids[3], "2026-10-02", "WITHDRAWAL", 52000.00, "Synthetic supplier payment"),
        ]
        cursor.executemany(
            """INSERT INTO transactions
               (account_id, transaction_date, transaction_type, amount, description)
               VALUES (%s, %s, %s, %s, %s)""",
            transactions
        )
        conn.commit()
    finally:
        conn.close()
