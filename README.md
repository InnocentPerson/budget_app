# Roommate Budget Splitter

A web app for splitting shared household expenses fairly among roommates, with an optimized settlement algorithm that minimizes the number of payments needed to settle all balances.

## Features

- **Expense tracking** — log shared expenses with payer, amount, and split participants
- **Settlement optimization** — computes the minimum number of transactions required to clear all outstanding group debts (instead of naive pairwise settling)
- **Ledger-style accounting** — all edits are handled through reversal journal entries rather than overwriting records, preserving a full, immutable audit trail
- **Atomic balance updates** — PostgreSQL transactional blocks ensure balances stay consistent even under concurrent edits from multiple roommates
- **Simple UI** — Bootstrap-based interface for adding expenses and viewing who owes whom

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | PostgreSQL |
| Frontend | Bootstrap, Jinja2 templates |

## How the Settlement Algorithm Works

Rather than settling every pairwise debt individually, the app nets out each person's total balance (total paid − total owed) and greedily matches the largest creditor with the largest debtor repeatedly. This reduces an arbitrary web of IOUs to the minimum possible number of transactions.

**Example:**
- Naive approach: A owes B ₹500, B owes C ₹500, C owes A ₹200 → 3 transactions
- Optimized: Net balances calculated first → reduces to 1–2 transactions

## Ledger Design

Expense edits don't overwrite existing rows. Instead, editing or deleting an expense creates a **reversal entry** that cancels the original, followed by a new entry if applicable. This means:
- Every historical state can be reconstructed
- No balance can silently drift due to an untracked edit
- Concurrent edits are safe because each entry is append-only

## Database Schema (simplified)

```sql
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    paid_by INT REFERENCES members(id),
    amount NUMERIC(10,2) NOT NULL,
    description TEXT,
    is_reversal BOOLEAN DEFAULT FALSE,
    reversed_expense_id INT REFERENCES expenses(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE expense_splits (
    expense_id INT REFERENCES expenses(id),
    member_id INT REFERENCES members(id),
    share NUMERIC(10,2) NOT NULL
);
```

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### Installation

```bash
git clone https://github.com/InnocentPerson/roommate-budget-splitter.git
cd roommate-budget-splitter
pip install -r requirements.txt
```

### Environment Setup

```
DATABASE_URL=postgresql://user:password@localhost:5432/budget_splitter
FLASK_APP=app.py
FLASK_ENV=development
```

### Database setup

```bash
flask db upgrade
```

### Run the app

```bash
flask run
```

Visit `http://localhost:5000` in your browser.

## Roadmap

- [ ] Recurring expense support
- [ ] Export settlement summary as PDF
- [ ] Multi-currency support

## License

MIT
