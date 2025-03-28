import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

try:
    # Connect to the database
    conn = sqlite3.connect('faction_manager.db')
    cursor = conn.cursor()
    
    # Check if decay_results table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decay_results';")
    table_exists = cursor.fetchone() is not None
    print(f"Decay results table exists: {table_exists}")
    
    if table_exists:
        # Check if there are any records
        cursor.execute("SELECT COUNT(*) FROM decay_results;")
        count = cursor.fetchone()[0]
        print(f"Number of records in decay_results: {count}")
        
        # Get a sample of records
        cursor.execute("SELECT * FROM decay_results LIMIT 5;")
        records = cursor.fetchall()
        print(f"Sample records: {records}")
    else:
        # Check if there are any tables at all
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        
        # Try to create the table
        print("Attempting to create the decay_results table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decay_results (
                    id TEXT PRIMARY KEY,
                    turn_number INTEGER NOT NULL,
                    district_id TEXT NOT NULL,
                    faction_id TEXT NOT NULL,
                    influence_change INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (district_id) REFERENCES districts (id),
                    FOREIGN KEY (faction_id) REFERENCES factions (id)
                )
            ''')
            conn.commit()
            print("Table created successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")
    
    conn.close()
except Exception as e:
    logging.error(f"Error: {e}") 