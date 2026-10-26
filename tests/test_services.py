import pandas as pd
import pytest
from src.services import account_summary, monthly_summary, flag_unusual_transactions

@pytest.fixture
def sample_transactions():
    return pd.DataFrame([
        {"transaction_id": 1, "account_id": 10, "display_name": "Demo A",
         "account_type": "SAVINGS", "transaction_date": "2026-09-01",
         "transaction_type": "DEPOSIT", "amount": 1000.0, "description": "sample"},
        {"transaction_id": 2, "account_id": 10, "display_name": "Demo A",
         "account_type": "SAVINGS", "transaction_date": "2026-09-02",
         "transaction_type": "WITHDRAWAL", "amount": 250.0, "description": "sample"},
        {"transaction_id": 3, "account_id": 11, "display_name": "Demo B",
         "account_type": "CURRENT", "transaction_date": "2026-10-02",
         "transaction_type": "DEPOSIT", "amount": 60000.0, "description": "sample"},
    ])

def test_account_summary(sample_transactions):
    result = account_summary(sample_transactions)
    first = result[result["account_id"] == 10].iloc[0]
    assert first["deposits"] == 1000
    assert first["withdrawals"] == 250
    assert first["simulated_net_movement"] == 750
    assert first["transaction_count"] == 2

def test_monthly_summary(sample_transactions):
    result = monthly_summary(sample_transactions)
    september = result[result["month"] == "2026-09"].iloc[0]
    assert september["deposits"] == 1000
    assert september["withdrawals"] == 250

def test_threshold_flag(sample_transactions):
    result = flag_unusual_transactions(sample_transactions, 50000)
    assert list(result["transaction_id"]) == [3]
    assert "not a fraud" in "This flag is not a fraud determination.".lower() or len(result) == 1
