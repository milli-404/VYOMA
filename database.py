import sqlite3

DB_NAME = "vyoma.db"

def get_connection():
    try:
        return sqlite3.connect(DB_NAME)
    except sqlite3.OperationalError as e:
        print(f"Error: Could not connect to database ({e}). Please ensure the database is accessible.")
        raise

def check_sessions_table():
    """Verify that the sessions table has the required columns, including accuracy, tx_hash, and injury_risk."""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("PRAGMA table_info(sessions)")
        columns = [info[1] for info in c.fetchall()]
        required_columns = {'id', 'user_id', 'sport', 'reward_points', 'status', 'accuracy', 'tx_hash', 'injury_risk'}
        conn.close()
        return required_columns.issubset(columns)
    except sqlite3.Error as e:
        print(f"Error checking sessions table schema: {e}")
        return False

def init_db():
    try:
        conn = get_connection()
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT UNIQUE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sport TEXT,
            reward_points INTEGER,
            status TEXT,
            accuracy REAL,
            tx_hash TEXT,
            injury_risk INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Add missing columns
        if not check_sessions_table():
            try:
                c.execute("ALTER TABLE sessions ADD COLUMN accuracy REAL")
                c.execute("ALTER TABLE sessions ADD COLUMN tx_hash TEXT")
                c.execute("ALTER TABLE sessions ADD COLUMN injury_risk INTEGER DEFAULT 0")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise e

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()