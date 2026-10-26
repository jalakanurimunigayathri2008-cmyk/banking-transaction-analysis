import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from src.db import get_connection, initialize_database, seed_demo_data
from src.services import (
    add_customer, add_account, record_transaction, fetch_customers,
    fetch_accounts, fetch_transactions, account_summary, monthly_summary,
    transaction_type_totals, flag_unusual_transactions
)

st.set_page_config(page_title="Banking Transaction Analysis", page_icon="🏦", layout="wide")

st.title("🏦 Banking Transaction Analysis System")
st.caption("Educational simulation using synthetic data only. Balances and reports are simulated.")

with st.sidebar:
    st.header("Database")
    st.write("Configure MySQL using the `.env` file.")
    if st.button("Initialize database tables"):
        try:
            initialize_database()
            st.success("Tables are ready.")
        except Exception as exc:
            st.error(f"Could not initialize database: {exc}")
    if st.button("Load synthetic demo data"):
        try:
            initialize_database()
            seed_demo_data()
            st.success("Demo data loaded (if not already present).")
        except Exception as exc:
            st.error(f"Could not load demo data: {exc}")

try:
    # Early connection check; services use short-lived connections too.
    conn = get_connection()
    conn.close()
except Exception as exc:
    st.error("Cannot connect to MySQL. Check that MySQL Server is running and your `.env` values are correct.")
    st.code(str(exc))
    st.stop()

try:
    customers = fetch_customers()
    accounts = fetch_accounts()
    transactions = fetch_transactions()
except Exception as exc:
    st.error(f"Could not read project data: {exc}")
    st.info("Use the sidebar buttons to initialize tables and load demo data.")
    st.stop()

tab_dashboard, tab_transactions, tab_customers, tab_accounts, tab_reports = st.tabs(
    ["Dashboard", "Transactions", "Customers", "Accounts", "Reports"]
)

with tab_dashboard:
    st.subheader("Overview")
    if transactions.empty:
        st.info("No transactions yet. Load synthetic demo data or add a transaction.")
    else:
        totals = transaction_type_totals(transactions)
        deposits = float(totals.get("DEPOSIT", 0))
        withdrawals = float(totals.get("WITHDRAWAL", 0))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Customers", len(customers))
        c2.metric("Accounts", len(accounts))
        c3.metric("Total deposits", f"₹{deposits:,.2f}")
        c4.metric("Total withdrawals", f"₹{withdrawals:,.2f}")

        left, right = st.columns(2)
        with left:
            st.markdown("**Deposits vs withdrawals**")
            fig, ax = plt.subplots()
            ax.bar(["Deposits", "Withdrawals"], [deposits, withdrawals])
            ax.set_ylabel("Amount (₹)")
            ax.set_title("Transaction totals")
            st.pyplot(fig)
            plt.close(fig)
        with right:
            st.markdown("**Transaction activity over time**")
            dated = transactions.copy()
            dated["transaction_date"] = pd.to_datetime(dated["transaction_date"])
            trend = dated.groupby(dated["transaction_date"].dt.to_period("M"))["amount"].sum()
            trend.index = trend.index.astype(str)
            fig, ax = plt.subplots()
            if not trend.empty:
                ax.plot(trend.index, trend.values, marker="o")
            ax.set_ylabel("Amount (₹)")
            ax.set_xlabel("Month")
            ax.set_title("Monthly transaction amount")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        st.markdown("**Latest transactions**")
        st.dataframe(transactions.head(10), use_container_width=True, hide_index=True)

with tab_transactions:
    st.subheader("Record a transaction")
    if accounts.empty:
        st.warning("Create an account first, or load demo data.")
    else:
        account_options = {
            f"Account {int(row.account_id)} — {row.display_name} ({row.account_type})": int(row.account_id)
            for row in accounts.itertuples()
        }
        with st.form("transaction_form"):
            selected_label = st.selectbox("Account", list(account_options.keys()))
            tx_type = st.selectbox("Transaction type", ["DEPOSIT", "WITHDRAWAL"])
            amount = st.number_input("Amount (₹)", min_value=0.01, value=100.00, step=50.00, format="%.2f")
            tx_date = st.date_input("Transaction date", value=date.today(), max_value=date.today())
            description = st.text_input("Description (optional)", max_chars=200)
            submitted = st.form_submit_button("Save transaction")
            if submitted:
                try:
                    record_transaction(account_options[selected_label], tx_type, Decimal(str(amount)), tx_date, description)
                    st.success("Transaction saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.markdown("**All transactions**")
    if not transactions.empty:
        type_filter = st.multiselect("Filter by type", ["DEPOSIT", "WITHDRAWAL"], default=["DEPOSIT", "WITHDRAWAL"])
        filtered = transactions[transactions["transaction_type"].isin(type_filter)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button(
            "Download transactions as CSV",
            filtered.to_csv(index=False).encode("utf-8"),
            file_name="transactions.csv",
            mime="text/csv"
        )
    else:
        st.info("No transaction records found.")

with tab_customers:
    st.subheader("Create a synthetic customer")
    with st.form("customer_form"):
        display_name = st.text_input("Display name", max_chars=100)
        customer_submit = st.form_submit_button("Create customer")
        if customer_submit:
            try:
                add_customer(display_name)
                st.success("Customer created.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    st.dataframe(customers, use_container_width=True, hide_index=True)

with tab_accounts:
    st.subheader("Create an account")
    if customers.empty:
        st.info("Create a customer first, or load demo data.")
    else:
        customer_options = {
            f"{row.display_name} (Customer {int(row.customer_id)})": int(row.customer_id)
            for row in customers.itertuples()
        }
        with st.form("account_form"):
            selected_customer = st.selectbox("Customer", list(customer_options.keys()))
            account_type = st.selectbox("Account type", ["SAVINGS", "CURRENT", "STUDENT"])
            account_submit = st.form_submit_button("Create account")
            if account_submit:
                try:
                    add_account(customer_options[selected_customer], account_type)
                    st.success("Account created.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    st.dataframe(accounts, use_container_width=True, hide_index=True)

with tab_reports:
    st.subheader("Account-wise summary")
    if transactions.empty:
        st.info("Add transactions to see reports.")
    else:
        summary = account_summary(transactions)
        st.dataframe(summary, use_container_width=True, hide_index=True)
        st.download_button("Download account summary CSV", summary.to_csv(index=False).encode("utf-8"),
                           file_name="account_summary.csv", mime="text/csv")

        st.subheader("Monthly summary")
        monthly = monthly_summary(transactions)
        st.dataframe(monthly, use_container_width=True, hide_index=True)
        st.download_button("Download monthly report CSV", monthly.to_csv(index=False).encode("utf-8"),
                           file_name="monthly_summary.csv", mime="text/csv")

        st.subheader("Rule-based unusual activity review")
        threshold = st.number_input("Flag transactions at or above (₹)", min_value=1.0, value=50000.0, step=5000.0)
        flagged = flag_unusual_transactions(transactions, threshold)
        if flagged.empty:
            st.success("No transactions matched this simple rule.")
        else:
            st.warning("These records only match a review rule. This is not a fraud determination.")
            st.dataframe(flagged, use_container_width=True, hide_index=True)
