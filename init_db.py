import sqlite3, time, os

DB_PATH = os.environ.get("DB_PATH", "app.db")

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL
)
""")

cur.execute("DELETE FROM items")
for i in range(1, 6):
    cur.execute("INSERT INTO items(name, created_at) VALUES (?, datetime('now'))", (f"item-{i}",))

con.commit()
con.close()

print(f"DB initialized at {DB_PATH}")