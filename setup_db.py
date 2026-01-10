import sqlite3
from datetime import datetime

# Connect to (or create) the database
db_name = 'ramadan_company.db'
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Create the contacts table
create_table_sql = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

try:
    cursor.execute(create_table_sql)
    print(f"Database '{db_name}' and table 'contacts' created successfully.")
    
    # Add a sample entry
    cursor.execute("""
        INSERT INTO contacts (full_name, phone_number, message, created_at)
        VALUES (?, ?, ?, ?)
    """, ("Test Client", "01234567890", "This is a test message to verify the database.", datetime.now()))
    
    conn.commit()
    print("Sample data inserted.")
    
except sqlite3.Error as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()
