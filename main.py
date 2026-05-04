from fastmcp import FastMCP
import aiosqlite
import os
import json
import csv

mcp = FastMCP(name="Expense Tracker")

# -------------------- PATH SETUP --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.getenv("DB_PATH", os.path.join("/tmp", "expense_tracker.db"))
categories_path = os.path.join(BASE_DIR, "categories.json")


# -------------------- INIT DB --------------------
async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        await db.commit()


# run init
import asyncio
asyncio.run(init_db())


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
async def add_expense(user_id: str, date: str, category: str, amount: float, subcategory: str = "", note: str = ""):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            INSERT INTO expenses (user_id, date, category, amount, subcategory, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, date, category, amount, subcategory, note))
        await db.commit()
        return {"status": "ok", "id": cur.lastrowid}


@mcp.tool
async def list_expenses(user_id: str, start_date: str, end_date: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT id, date, category, amount, subcategory, note
            FROM expenses
            WHERE user_id=? AND date BETWEEN ? AND ?
            ORDER BY id ASC
        """, (user_id, start_date, end_date))
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


@mcp.tool
async def summary(user_id: str, start_date: str, end_date: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id=? AND date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
        """, (user_id, start_date, end_date))
        rows = await cur.fetchall()
        return [dict(zip(["category", "amount"], row)) for row in rows]


@mcp.tool
async def update_expense(user_id: str, id: int, date=None, category=None, amount=None, subcategory=None, note=None):
    async with aiosqlite.connect(db_path) as db:
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

        values.extend([user_id, id])

        await db.execute(
            f"UPDATE expenses SET {', '.join(fields)} WHERE user_id=? AND id=?",
            values
        )
        await db.commit()
        return {"status": "updated"}


@mcp.tool
async def delete_expense(user_id: str, id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "DELETE FROM expenses WHERE user_id=? AND id=?",
            (user_id, id)
        )
        await db.commit()
        return {"status": "deleted"}


@mcp.tool
async def total_spent(user_id: str, start_date: str, end_date: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE user_id=? AND date BETWEEN ? AND ?
        """, (user_id, start_date, end_date))
        val = await cur.fetchone()
        return {"total": val[0] or 0}


@mcp.tool
async def category_spending(user_id: str, category: str, start_date: str, end_date: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE user_id=? AND category=? AND date BETWEEN ? AND ?
        """, (user_id, category, start_date, end_date))
        val = await cur.fetchone()
        return {"category": category, "amount": val[0] or 0}


@mcp.tool
async def monthly_summary(user_id: str, year: int, month: int):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id=? AND strftime('%Y', date)=?
              AND strftime('%m', date)=?
            GROUP BY category
        """, (user_id, str(year), f"{month:02d}"))
        rows = await cur.fetchall()
        return [dict(zip(["category", "amount"], row)) for row in rows]


@mcp.tool
async def search_expenses(user_id: str, keyword: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT * FROM expenses
            WHERE user_id=? AND (category LIKE ? OR note LIKE ?)
        """, (user_id, f"%{keyword}%", f"%{keyword}%"))
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


@mcp.tool
async def filter_by_amount(user_id: str, min_amount: float, max_amount: float):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT * FROM expenses
            WHERE user_id=? AND amount BETWEEN ? AND ?
        """, (user_id, min_amount, max_amount))
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


@mcp.tool
async def daily_spending(user_id: str, start_date: str, end_date: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT date, SUM(amount)
            FROM expenses
            WHERE user_id=? AND date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (user_id, start_date, end_date))
        rows = await cur.fetchall()
        return [dict(zip(["date", "amount"], row)) for row in rows]


@mcp.tool
async def budget_check(user_id: str, category: str, limit: float, start_date: str, end_date: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE user_id=? AND category=? AND date BETWEEN ? AND ?
        """, (user_id, category, start_date, end_date))
        spent = (await cur.fetchone())[0] or 0

        return {
            "category": category,
            "spent": spent,
            "limit": limit,
            "status": "exceeded" if spent > limit else "within budget"
        }


@mcp.tool
async def highest_expense(user_id: str):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT * FROM expenses
            WHERE user_id=?
            ORDER BY amount DESC
            LIMIT 1
        """, (user_id,))
        row = await cur.fetchone()
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row)) if row else {}


@mcp.tool
async def top_categories(user_id: str, limit: int = 3):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id=?
            GROUP BY category
            ORDER BY total DESC
            LIMIT ?
        """, (user_id, limit))
        rows = await cur.fetchall()
        return [dict(zip(["category", "total"], row)) for row in rows]


@mcp.tool
async def export_csv(user_id: str, filename: str = "expenses.csv"):
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT * FROM expenses WHERE user_id=?
        """, (user_id,))
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)

    return {"status": "exported", "file": filename}


# -------------------- RUN SERVER --------------------
if __name__ == "__main__":
    print("🚀 MCP Server running at ws://0.0.0.0:8000")
    mcp.run(transport="ws", host="0.0.0.0", port=8000)