
import sqlite3

DATABASE_NAME = "finance.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def create_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL
                    CHECK(type IN ('Income', 'Expense')),
                colour TEXT NOT NULL DEFAULT '#0D9488',
                UNIQUE(name, type)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount_pence INTEGER NOT NULL
                    CHECK(amount_pence > 0),
                type TEXT NOT NULL
                    CHECK(type IN ('Income', 'Expense')),
                category_id INTEGER,
                date TEXT NOT NULL,
                FOREIGN KEY (category_id)
                    REFERENCES categories(id)
            )
        """)

        conn.commit()


def add_transaction(
    description,
    amount_pence,
    transaction_type,
    date,
    category_id=None,
):
    """Save a transaction with its selected category."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions
                (description, amount_pence, type, date, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            description,
            amount_pence,
            transaction_type,
            date,
            category_id,
        ))
        conn.commit()




def get_transactions():
    """Retrieve transactions with category names, newest first."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT
                t.id,
                t.description,
                t.amount_pence,
                t.type,
                t.date,
                COALESCE(c.name, 'Uncategorised') AS category
            FROM transactions AS t
            LEFT JOIN categories AS c
                ON t.category_id = c.id
            ORDER BY t.date DESC, t.id DESC
        """).fetchall()



def get_balance_summary():
    """Calculate income, expenses and remaining balance."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT type, COALESCE(SUM(amount_pence), 0)
            FROM transactions
            GROUP BY type
        """).fetchall()

    totals = dict(rows)

    income = totals.get("Income", 0)
    expenses = totals.get("Expense", 0)
    balance = income - expenses

    return income, expenses, balance



def add_category(name, category_type, colour="#0D9488"):
    """Create a new income or expense category."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO categories (name, type, colour)
            VALUES (?, ?, ?)
        """, (name, category_type, colour))
        conn.commit()


def get_categories(category_type=None):
    """Retrieve categories, optionally filtered by type."""
    with get_connection() as conn:
        if category_type:
            return conn.execute("""
                SELECT id, name, type, colour
                FROM categories
                WHERE type = ?
                ORDER BY name
            """, (category_type,)).fetchall()

        return conn.execute("""
            SELECT id, name, type, colour
            FROM categories
            ORDER BY type, name
        """).fetchall()


def rename_category(category_id, new_name):
    """Rename an existing category."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE categories
            SET name = ?
            WHERE id = ?
        """, (new_name, category_id))
        conn.commit()


def delete_category(category_id):
    """Delete a category only if no transactions use it."""
    with get_connection() as conn:
        count = conn.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE category_id = ?
        """, (category_id,)).fetchone()[0]

        if count > 0:
            return False

        conn.execute(
            "DELETE FROM categories WHERE id = ?",
            (category_id,),
        )
        conn.commit()

        return True


def seed_default_categories():
    """Add starter categories without duplicating existing ones."""
    defaults = {
        "Income": [
            "Salary", "Bonus", "Freelance",
            "Other Income"
        ],
        "Expense": [
            "Rent", "Groceries", "Transport",
            "Bills", "Shopping", "Entertainment",
            "Subscriptions", "Healthcare", "Other"
        ],
    }

    with get_connection() as conn:
        for category_type, names in defaults.items():
            for name in names:
                conn.execute("""
                    INSERT OR IGNORE INTO categories
                        (name, type)
                    VALUES (?, ?)
                """, (name, category_type))

        conn.commit()



def delete_transaction(transaction_id):
    """Delete a transaction using its unique ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

def update_transaction(transaction_id, description, amount_pence, transaction_type, transaction_date, category_id):
    """Update an existing transaction using its unique ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE transactions
            SET description = ?,
                amount_pence = ?,
                type = ?,
                date = ?,
                category_id = ?
            WHERE id = ?
            """,
            (
                description,
                amount_pence,
                transaction_type,
                transaction_date,
                category_id,
                transaction_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
