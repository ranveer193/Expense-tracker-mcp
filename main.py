from fastmcp import FastMCP
import sqlite3
import os
import json

mcp = FastMCP(name = "Expense Tracker")
db_path = os.path.join(os.path.dirname(__file__), "expense_tracker.db")
categories_path = os.path.join(os.path.dirname(__file__), "categories.json")

def init_db():
    with sqlite3.connect(db_path) as c:
        c.execute("""
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

@mcp.resource(
    uri="resource://categories",
    mime_type="application/json"
)
def categories():
    """List of available expense categories"""
    try:
        with open(categories_path, "r") as f:
            data = json.load(f)
            return data
    except Exception as e:
        return {"error": str(e)}
    
@mcp.tool
def add_expense(date : str, category : str, amount : float, subcategory="", note=""):
    """Add an expense to the database"""
    with sqlite3.connect(db_path) as c:
        cur = c.execute("""
            INSERT INTO expenses (date, category, amount, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
        """, (date, category, amount, subcategory, note))
        return {"status" : "ok","id":cur.lastrowid}

@mcp.tool
def list_expenses(start_date: str, end_date : str):
    """List all expenses in the database between start_date and end_date"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT id, date, category, amount, subcategory, note FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
        """, (start_date, end_date))
        cols = [d[0] for d in curr.description]
        return [dict(zip(cols, row)) for row in curr.fetchall()]
    
@mcp.tool
def summary(start_date: str, end_date : str):
    """Return a summary of expenses between start_date and end_date"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT category, SUM(amount) FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
        """, (start_date, end_date))
        return [dict(zip(["category", "amount"], row)) for row in curr.fetchall()]
    
@mcp.tool
def update_expense(id: int, date=None, category=None, amount=None, subcategory=None, note=None):
    """Update an existing expense"""
    with sqlite3.connect(db_path) as c:
        fields = []
        values = []

        if date:
            fields.append("date=?")
            values.append(date)
        if category:
            fields.append("category=?")
            values.append(category)
        if amount:
            fields.append("amount=?")
            values.append(amount)
        if subcategory is not None:
            fields.append("subcategory=?")
            values.append(subcategory)
        if note is not None:
            fields.append("note=?")
            values.append(note)

        values.append(id)

        c.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id=?", values)
        return {"status": "updated"}
    
@mcp.tool
def delete_expense(id: int):
    """Delete an expense"""
    with sqlite3.connect(db_path) as c:
        c.execute("DELETE FROM expenses WHERE id=?", (id,))
        return {"status": "deleted"}
    
@mcp.tool
def total_spent(start_date: str, end_date: str):
    """Get total spending in date range"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT SUM(amount) FROM expenses
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        return {"total": curr.fetchone()[0] or 0}
    
@mcp.tool
def category_spending(category: str, start_date: str, end_date: str):
    """Total spending for a category"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT SUM(amount) FROM expenses
            WHERE category=? AND date BETWEEN ? AND ?
        """, (category, start_date, end_date))
        return {"category": category, "amount": curr.fetchone()[0] or 0}
    

@mcp.tool
def monthly_summary(year: int, month: int):
    """Monthly summary by category"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE strftime('%Y', date)=?
              AND strftime('%m', date)=?
            GROUP BY category
        """, (str(year), f"{month:02d}"))
        return [dict(zip(["category", "amount"], row)) for row in curr.fetchall()]
    
@mcp.tool
def search_expenses(keyword: str):
    """Search by note or category"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT * FROM expenses
            WHERE category LIKE ? OR note LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%"))
        cols = [d[0] for d in curr.description]
        return [dict(zip(cols, row)) for row in curr.fetchall()]
    

@mcp.tool
def filter_by_amount(min_amount: float, max_amount: float):
    """Filter expenses by amount range"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT * FROM expenses
            WHERE amount BETWEEN ? AND ?
        """, (min_amount, max_amount))
        cols = [d[0] for d in curr.description]
        return [dict(zip(cols, row)) for row in curr.fetchall()]
    
@mcp.tool
def daily_spending(start_date: str, end_date: str):
    """Daily spending trend"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT date, SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))
        return [dict(zip(["date", "amount"], row)) for row in curr.fetchall()]
    
@mcp.tool
def budget_check(category: str, limit: float, start_date: str, end_date: str):
    """Check if budget exceeded"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE category=? AND date BETWEEN ? AND ?
        """, (category, start_date, end_date))

        spent = curr.fetchone()[0] or 0

        return {
            "category": category,
            "spent": spent,
            "limit": limit,
            "status": "exceeded" if spent > limit else "within budget"
        }
    
@mcp.tool
def highest_expense():
    """Get highest single expense"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT * FROM expenses
            ORDER BY amount DESC LIMIT 1
        """)
        row = curr.fetchone()
        cols = [d[0] for d in curr.description]
        return dict(zip(cols, row)) if row else {}
    
@mcp.tool
def top_categories(limit: int = 3):
    """Top spending categories"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            LIMIT ?
        """, (limit,))
        return [dict(zip(["category", "total"], row)) for row in curr.fetchall()]
    
import csv

@mcp.tool
def export_csv(filename: str = "expenses.csv"):
    """Export all expenses to CSV"""
    with sqlite3.connect(db_path) as c:
        curr = c.execute("SELECT * FROM expenses")
        cols = [d[0] for d in curr.description]
        rows = curr.fetchall()

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)

    return {"status": "exported", "file": filename}
    

if __name__ == "__main__":
    mcp.run()