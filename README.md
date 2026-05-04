# 🧾 Expense Tracker MCP Server

A lightweight, production-ready **Model Context Protocol (MCP) server** that enables AI agents to manage, query, and analyze personal expense data in real time.

---

## 🚀 Overview

This project implements a fully functional **expense tracking backend** exposed via MCP, allowing AI assistants (like Claude, Windsurf, etc.) to interact with financial data through structured tools.

It combines:

* 🧠 AI-compatible tool interface (MCP)
* 💾 Local persistent storage (SQLite)
* ⚡ Real-time remote access (WebSocket)

---

## ✨ Features

* ➕ Add, update, and delete expenses
* 📋 List expenses within date ranges
* 📊 Category-wise and monthly summaries
* 💰 Total spending and budget checks
* 🔍 Search expenses by keyword
* 📈 Daily spending trends
* 🏆 Top categories and highest expense
* 📤 Export all data to CSV
* 📂 Predefined categories via MCP resource

---

## 🧠 MCP Capabilities

| Type          | Description                                     |
| ------------- | ----------------------------------------------- |
| **Tools**     | 15+ functions for full expense management       |
| **Resource**  | `resource://categories` (JSON-based categories) |
| **Transport** | WebSocket (`ws://`) for remote connectivity     |

---

## 🏗️ Tech Stack

* **Python**
* **SQLite**
* **FastMCP**

---

## 📁 Project Structure

```bash
.
├── server.py
├── expense_tracker.db
├── categories.json
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/expense-tracker-mcp.git
cd expense-tracker-mcp
```

---

### 2️⃣ Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

---

### 3️⃣ Install dependencies

```bash
pip install fastmcp
```

---

### 4️⃣ Run the server

```bash
python server.py
```

---

## 🌐 Connect to Server

Use WebSocket:

```bash
ws://localhost:8000
```

For remote access:

```bash
ws://<your-ip>:8000
```

//inspect command
uv run fastmcp dev inspector main.py

//apps command
uv run fastmcp dev apps main.py

//run command
uv run fastmcp run main.py

---

## 🧪 Example Tool Usage

### Add Expense

```json
{
  "date": "2026-05-01",
  "category": "Food",
  "amount": 250,
  "note": "Lunch"
}
```

---

### Get Summary

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-31"
}
```

---

## 🎯 Use Cases

* Personal finance tracking
* AI-powered budgeting assistants
* Expense analytics dashboards
* MCP server learning project

---

## 🔥 Why this project matters

This project demonstrates:

* Building **real-world MCP servers**
* Designing **AI-consumable APIs**
* Managing structured data with minimal dependencies
* Enabling **agent-driven financial insights**

---

## 🚧 Future Improvements

* Authentication & user accounts
* Cloud database support (PostgreSQL)
* REST + MCP hybrid API
* Visualization dashboard

---

## 🤝 Contributing

Pull requests are welcome! Feel free to open issues for suggestions or improvements.

---

## 📜 License

This project is open-source and available under the MIT License.

---

## ⭐ Support

If you found this useful, consider giving it a star ⭐ on GitHub!
