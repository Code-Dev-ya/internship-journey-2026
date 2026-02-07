import sqlite3

def create_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        email TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        name TEXT,
        department TEXT,
        degree TEXT,
        year INTEGER,
        gender TEXT,
        bio TEXT,
        interests TEXT
    )
    """)

    # FOLLOW REQUESTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS follow_requests (
        sender_email TEXT,
        receiver_email TEXT,
        status TEXT,
        PRIMARY KEY (sender_email, receiver_email)
    )
    """)

    conn.commit()
    conn.close()
