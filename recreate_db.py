import sqlite3

def recreate_donations_table():
    try:
        with sqlite3.connect('donations.db') as conn:
            cursor = conn.cursor()
            
            # Drop existing table
            cursor.execute('DROP TABLE IF EXISTS donations')
            
            # Create table with all required columns
            cursor.execute('''
                CREATE TABLE donations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    donor_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    is_recurring BOOLEAN DEFAULT 0,
                    recurring_interval TEXT,
                    next_donation_date TEXT
                )
            ''')
            
            conn.commit()
            print('Successfully recreated donations table')
            
    except Exception as e:
        print(f'Error recreating database: {str(e)}')

if __name__ == '__main__':
    recreate_donations_table()