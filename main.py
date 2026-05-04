from fastmcp import FastMCP
import sqlite3
import os
import json
import csv

mcp = FastMCP(name="Expense Tracker")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "expense_tracker.db")
categories_path = os.path.join(BASE_DIR, "categories.json")


# -------------------- INIT DB --------------------
def init_db():
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()


# -------------------- RESOURCE --------------------
@mcp.resource(uri="resource://categories", mime_type="application/json")
def categories():
    try:
        if not os.path.exists(categories_path):
            return {"error": "categories.json not found"}
        with open(categories_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


# -------------------- TOOLS --------------------

@mcp.tool
def add_expense(date: str, category: str, amount: float, subcategory: str = "", note: str = ""):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            INSERT INTO expenses (date, category, amount, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
        """, (date, category, amount, subcategory, note))
        return {"status": "ok", "id": cur.lastrowid}


@mcp.tool
def list_expenses(start_date: str, end_date: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT id, date, category, amount, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
        """, (start_date, end_date))

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


@mcp.tool
def summary(start_date: str, end_date: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
        """, (start_date, end_date))

        return [dict(zip(["category", "amount"], row)) for row in cur.fetchall()]


@mcp.tool
def update_expense(id: int, date=None, category=None, amount=None, subcategory=None, note=None):
    with sqlite3.connect(db_path) as conn:
        fields = []
        values = []

        if date is not None:
            fields.append("date=?")
            values.append(date)
        if category is not None:
            fields.append("category=?")
            values.append(category)
        if amount is not None:
            fields.append("amount=?")
            values.append(amount)
        if subcategory is not None:
            fields.append("subcategory=?")
            values.append(subcategory)
        if note is not None:
            fields.append("note=?")
            values.append(note)

        if not fields:
            return {"status": "no fields to update"}

        values.append(id)

        conn.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id=?", values)
        return {"status": "updated"}


@mcp.tool
def delete_expense(id: int):
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (id,))
        return {"status": "deleted"}


@mcp.tool
def total_spent(start_date: str, end_date: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))

        return {"total": cur.fetchone()[0] or 0}


@mcp.tool
def category_spending(category: str, start_date: str, end_date: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE category=? AND date BETWEEN ? AND ?
        """, (category, start_date, end_date))

        return {"category": category, "amount": cur.fetchone()[0] or 0}


@mcp.tool
def monthly_summary(year: int, month: int):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE strftime('%Y', date)=?
              AND strftime('%m', date)=?
            GROUP BY category
        """, (str(year), f"{month:02d}"))

        return [dict(zip(["category", "amount"], row)) for row in cur.fetchall()]


@mcp.tool
def search_expenses(keyword: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT * FROM expenses
            WHERE category LIKE ? OR note LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%"))

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


@mcp.tool
def filter_by_amount(min_amount: float, max_amount: float):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT * FROM expenses
            WHERE amount BETWEEN ? AND ?
        """, (min_amount, max_amount))

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


@mcp.tool
def daily_spending(start_date: str, end_date: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT date, SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))

        return [dict(zip(["date", "amount"], row)) for row in cur.fetchall()]


@mcp.tool
def budget_check(category: str, limit: float, start_date: str, end_date: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE category=? AND date BETWEEN ? AND ?
        """, (category, start_date, end_date))

        spent = cur.fetchone()[0] or 0

        return {
            "category": category,
            "spent": spent,
            "limit": limit,
            "status": "exceeded" if spent > limit else "within budget"
        }


@mcp.tool
def highest_expense():
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT * FROM expenses
            ORDER BY amount DESC
            LIMIT 1
        """)

        row = cur.fetchone()
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row)) if row else {}


@mcp.tool
def top_categories(limit: int = 3):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            LIMIT ?
        """, (limit,))

        return [dict(zip(["category", "total"], row)) for row in cur.fetchall()]


@mcp.tool
def export_csv(filename: str = "expenses.csv"):
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT * FROM expenses")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)

    return {"status": "exported", "file": filename}


# -------------------- RUN SERVER --------------------
if __name__ == "__main__":
    print("🚀 MCP Expense Tracker running on http://0.0.0.0:8000/mcp")
    mcp.run(transport="http", host="0.0.0.0", port=8000)