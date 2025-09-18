import sqlite3
import re
from database import get_connection

def is_valid_email(email):
    """Validate email format using regex."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_user_id(user_id):
    """Validate if user_id exists in the users table."""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE id=?", (user_id,))
        user = c.fetchone()
        conn.close()
        return user is not None
    except sqlite3.Error as e:
        print(f"Error validating user ID: {e}")
        return False

def register_user(name, phone, email):
    """Register a user after validating email."""
    if not is_valid_email(email):
        raise ValueError("Invalid email format. Please provide a valid email (e.g., user@domain.com).")
    
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        if c.fetchone():
            conn.close()
            raise ValueError("Email already registered. Please use a different email.")
        c.execute("INSERT INTO users (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error saving user to database: {e}")
        raise

def get_user(email):
    """Retrieve a user by email after validating format."""
    if not is_valid_email(email):
        return None  # Return None for invalid email to trigger registration prompt
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        return user
    except sqlite3.Error as e:
        print(f"Error retrieving user from database: {e}")
        return None