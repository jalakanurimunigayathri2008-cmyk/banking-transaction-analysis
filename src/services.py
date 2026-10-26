from decimal import Decimal, InvalidOperation
import pandas as pd
from src.db import get_connection

def add_customer(display_name):
    name = (display_name or "").strip()
    if not name:
        raise ValueError("Display name cannot be empty.")
    if len(name) > 100:
        raise ValueError("Display name must be 100 characters or fewer.")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO customers (display_name) VALUES (%s)", (name,))
        conn.commit()
    finally:
        conn.close()

def add_account(customer_id, account_type):
    allowed = {"SAVINGS", "CURRENT", "STUDENT"}
    kind = str(account_type).upper()
    if kind not in allowed:
        raise ValueError("Choose a valid account type.")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (customer_id,))
        if cur.fetchone() is None:
            raise ValueError("Selected customer does not exist.")
        cur.execute("INSERT INTO accounts (customer_id, account_type) VALUES (%s, %s)", (customer_id, kind))
        conn.commit()
    finally:
        conn.close()

def record_transaction(account_id, transaction_type, amount, transaction_date, description=""):
    kind = str(transaction_type).upper()
    if kind not in {"DEPOSIT", "WITHDRAWAL"}:
        raise ValueError("Transaction type must be DEPOSIT or WITHDRAWAL.")
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid numeric amount.")
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    if value.quantize(Decimal("0.01")) != value:
        raise ValueError("Amount can have at most two decimal places.")
    if value > Decimal("9999999999.99"):
        raise ValueError("Amount is too large.")
    if not transaction_date:
        raise ValueError("Transaction date is required.")
    description = (description or "").strip()[:200] or None

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM accounts WHERE account_id = %s", (account_id,))
        if cur.fetchone() is None:
            raise ValueError("Selected account does not exist.")
        cur.execute(
            """INSERT INTO transactions
               (account_id, transaction_date, transaction_type, amount, description)
               VALUES (%s, %s, %s, %s, %s)""",
            (account_id, transaction_date, kind, str(value), description)
        )
        conn.commit()
    finally:
        conn.close()

def _read_query(query, params=None):
    conn = get_connection()
    try:
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()

def fetch_customers():
    return _read_query("SELECT customer_id, display_name, created_at FROM customers ORDER BY customer_id DESC")

def fetch_accounts():
    return _read_query(
        """SELECT a.account_id, a.customer_id, c.display_name, a.account_type, a.created_at
           FROM accounts a JOIN customers c ON a.customer_id = c.customer_id
           ORDER BY a.account_id DESC"""
    )

def fetch_transactions():
    return _read_query(
        """SELECT t.transaction_id, t.account_id, c.display_name, a.account_type,
                  t.transaction_date, t.transaction_type, t.amount, t.description
           FROM transactions t
           JOIN accounts a ON t.account_id = a.account_id
           JOIN customers c ON a.customer_id = c.customer_id
           ORDER BY t.transaction_date DESC, t.transaction_id DESC"""
    )

def transaction_type_totals(transactions):
    if transactions.empty:
        return {}
    totals = transactions.groupby("transaction_type")["amount"].sum()
    return {str(k): float(v) for k, v in totals.items()}

def account_summary(transactions):
    if transactions.empty:
        return pd.DataFrame(columns=[
            "account_id", "display_name", "account_type", "deposits",
            "withdrawals", "simulated_net_movement", "transaction_count"
        ])
    data = transactions.copy()
    data["amount"] = pd.to_numeric(data["amount"])
    data["deposit_amount"] = data["amount"].where(data["transaction_type"] == "DEPOSIT", 0)
    data["withdrawal_amount"] = data["amount"].where(data["transaction_type"] == "WITHDRAWAL", 0)
    result = data.groupby(["account_id", "display_name", "account_type"], as_index=False).agg(
        deposits=("deposit_amount", "sum"),
        withdrawals=("withdrawal_amount", "sum"),
        transaction_count=("transaction_id", "count")
    )
    result["simulated_net_movement"] = result["deposits"] - result["withdrawals"]
    return result.round(2)

def monthly_summary(transactions):
    if transactions.empty:
        return pd.DataFrame(columns=["month", "deposits", "withdrawals", "net_movement", "transaction_count"])
    data = transactions.copy()
    data["amount"] = pd.to_numeric(data["amount"])
    data["transaction_date"] = pd.to_datetime(data["transaction_date"])
    data["month"] = data["transaction_date"].dt.to_period("M").astype(str)
    data["deposits"] = data["amount"].where(data["transaction_type"] == "DEPOSIT", 0)
    data["withdrawals"] = data["amount"].where(data["transaction_type"] == "WITHDRAWAL", 0)
    result = data.groupby("month", as_index=False).agg(
        deposits=("deposits", "sum"),
        withdrawals=("withdrawals", "sum"),
        transaction_count=("transaction_id", "count")
    )
    result["net_movement"] = result["deposits"] - result["withdrawals"]
    return result.round(2)

def flag_unusual_transactions(transactions, threshold=50000):
    """Simple amount threshold for human review; not a fraud detector."""
    if transactions.empty:
        return transactions.copy()
    result = transactions[pd.to_numeric(transactions["amount"]) >= float(threshold)].copy()
    result["review_reason"] = f"Amount is at or above the configured threshold (₹{float(threshold):,.2f})"
    return result
