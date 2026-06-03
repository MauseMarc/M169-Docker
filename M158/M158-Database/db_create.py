from database.db_base import *
conn = get_db()

# Create Asset Table
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS asset ( 
        id INTEGER PRIMARY KEY, 
        asset_name TEXT,
        asset_code TEXT,
        category TEXT
        );
    """)
    conn.commit()

#Create Company Table
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS company ( 
        id INTEGER PRIMARY KEY,
        company_name TEXT,
        company_type TEXT,
        asset_id INTEGER,
        code TEXT,
        FOREIGN KEY (asset_id) REFERENCES asset (id)
        );
    """)
    conn.commit()

# Create Ledger Table
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS ledger ( 
        id INTEGER PRIMARY KEY, 
        timestamp TEXT,
        sender_id INTEGER,
        recipient_id INTEGER,
        amount INTEGER,
        asset_id INTEGER,
        detail TEXT,
        FOREIGN KEY (sender_id) REFERENCES company (id),
        FOREIGN KEY (recipient_id) REFERENCES company (id),
        FOREIGN KEY (asset_id) REFERENCES asset (id)
        );
    """)
    conn.commit()

# Stock Ledger (like the worth of any stock at any given time or something. To make graphs and stuff)
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS stock_ledger ( 
        id INTEGER PRIMARY KEY, 
        timestamp TEXT,
        asset_id INTEGER,
        worth INTEGER,
        FOREIGN KEY (asset_id) REFERENCES asset (id)
        );
    """)
    conn.commit()

# loan Table
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS loan ( 
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        company_id INTEGER,
        asset_id INTEGER,
        amount INTEGER,
        interest_rate INTEGER,
        ongoing BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (company_id) REFERENCES company (id),
        FOREIGN KEY (asset_id) REFERENCES asset (id)
        );
    """)
    conn.commit()

# Inventions
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS invention ( 
        id INTEGER PRIMARY KEY, 
        timestamp TEXT,
        asset_id INTEGER,
        creator_id INTEGER,
        investor_id INTEGER,
        percentage INTEGER,
        vote_score INTEGER,
        funding_amount INTEGER,
        FOREIGN KEY (creator_id) REFERENCES company (id),
        FOREIGN KEY (investor_id) REFERENCES company (id),
        FOREIGN KEY (asset_id) REFERENCES asset (id)
        );
    """)
    conn.commit()


# Create the three Event important Tables
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS event (
        id INTEGER PRIMARY KEY, 
        status_id INTEGER,
        event_title TEXT,
        story_type TEXT,
        duration INTEGER,
        severity INTEGER,
        target BOOLEAN DEFAULT FALSE,
        price INTEGER,
        FOREIGN KEY (status_id) REFERENCES status (id)
        );
    """)
    conn.commit()
with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS active_event (
        id INTEGER PRIMARY KEY, 
        timestamp TEXT,
        affected_id INTEGER,
        event_id INTEGER,
        story_id INTEGER,
        duration_s TEXT,
        FOREIGN KEY (affected_id) REFERENCES company (id),
        FOREIGN KEY (event_id) REFERENCES event (id)
        FOREIGN KEY (story_id) REFERENCES story (id)
        );
    """)
    conn.commit()

with conn:
    cursor = conn.cursor()
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS story (
    id INTEGER PRIMARY KEY,
    story_type TEXT,
    story_title TEXT,
    story_text TEXT
    );
    """)
    conn.commit()