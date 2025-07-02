# database.py
import sqlite3

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        cur = self.conn.cursor()
        # existing table creations...
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT,
                amount REAL NOT NULL,
                note TEXT
            )
        """)
        self.conn.commit()
    

    def cursor(self):
        return self.conn.cursor()
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()
