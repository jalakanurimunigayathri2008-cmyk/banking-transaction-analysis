# Banking Transaction Analysis System

An educational Python + MySQL project for recording **synthetic** transactions and analysing deposits, withdrawals, monthly activity, and account-level summaries.

> **Safety boundary:** This is not a real banking platform. Use synthetic/demo data only. Do not enter real customer information, account numbers, credentials, or sensitive financial information. Net movement shown by this project is a simulated calculation from the transactions present; it is not a verified bank balance. Rule-based flags are only for human review and do not establish fraud.

## Features

- Create synthetic customer and account records.
- Record deposits and withdrawals with validation.
- Store records in MySQL using parameterized queries.
- View account-wise deposits, withdrawals, net movement, and transaction count.
- Generate monthly summaries and charts.
- Export transaction and report tables as CSV.
- Flag transactions above a configurable amount threshold for review.
- Include tests for summary calculations.

## Technology stack

- Python
- Streamlit
- MySQL
- Pandas and NumPy
- Matplotlib
- pytest

## Folder structure

```text
banking-transaction-analysis/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── database/
│   └── schema.sql
├── src/
│   ├── __init__.py
│   ├── db.py
│   └── services.py
└── tests/
    └── test_services.py
```

## Prerequisites

1. Python 3.10 or newer.
2. MySQL Server installed and running.
3. Git installed.
4. A local MySQL account that can create/use the project database.

## Setup on Windows (PowerShell)

Open PowerShell in the project folder.

### 1. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the environment's Python directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create the local environment file

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace the example password with your local MySQL password. Do not commit `.env` to Git.

### 4. Create the database

Option A: Open MySQL Workbench, connect to your local MySQL server, open `database/schema.sql`, and execute it.

Option B: In a MySQL command-line client, run:

```sql
CREATE DATABASE IF NOT EXISTS banking_analysis;
```

The app's **Initialize database tables** button creates the tables inside this database.

### 5. Start the app

```powershell
streamlit run app.py
```

Streamlit should print a local URL, usually `http://localhost:8501`. Open it in your browser.

### 6. Load demo records

In the app sidebar:
1. Click **Initialize database tables**.
2. Click **Load synthetic demo data**.

The demo loader inserts sample records only when the customers table is empty. If you already have data, it will not add the demo set again.

## Run tests

```powershell
pytest -q
```

Tests exercise report calculations and the threshold review rule; they do not require a live database.

## How calculations work

- **Deposits:** sum of transactions whose type is `DEPOSIT`.
- **Withdrawals:** sum of transactions whose type is `WITHDRAWAL`.
- **Simulated net movement:** deposits minus withdrawals for the records available.
- **Monthly summary:** groups transactions by calendar month.
- **Review flag:** marks a transaction whose amount meets or exceeds a configurable threshold. This simple rule can produce false positives and is not fraud detection.

## Push the project to GitHub

1. Create a new empty repository on GitHub, for example `banking-transaction-analysis`. Do not initialize it with a README if you already have this README locally.
2. In PowerShell, from the project folder:

```powershell
git init
git add .
git status
git commit -m "Initial commit: banking transaction analysis system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/banking-transaction-analysis.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. GitHub may ask you to authenticate in a browser or through Git Credential Manager.

### Before pushing

Run:

```powershell
git status
```

Check that `.env` is **not** listed among files to be committed. `.gitignore` excludes it, but always check before pushing.

If you accidentally staged `.env` before adding it to `.gitignore`, unstage it with:

```powershell
git rm --cached .env
```

If you already pushed a secret, removing the file in a later commit is not enough: rotate that password/secret and follow GitHub's guidance for removing sensitive data from history.

## Common issues

- **Access denied for MySQL user:** verify `DB_USER` and `DB_PASSWORD` in `.env`.
- **Unknown database:** create `banking_analysis` first using MySQL Workbench or `CREATE DATABASE`.
- **Can't connect to MySQL:** ensure the MySQL Server service is running and `DB_PORT` is correct.
- **`streamlit` not recognized:** activate `.venv` or run `python -m streamlit run app.py`.
- **Import errors:** run commands from the project root, where `app.py` is located.

## Limitations

This is a learning prototype, not production banking software. It does not implement authentication, authorization by user role, audit-grade immutable records, reconciliation, regulatory compliance, or real-time fraud detection. Do not expose it publicly with an unprotected database.
