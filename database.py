import os
import sqlite3
import threading
from queue import Queue
from typing import List, Dict, Any

class DonationDatabase:
    _instance = None
    _lock = threading.Lock()
    _connection_pool = Queue(maxsize=5)
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DonationDatabase, cls).__new__(cls)
                    cls._instance._initialize_pool()
        return cls._instance
    
    def _initialize_pool(self):
        for _ in range(5):
            conn = sqlite3.connect('donations.db', check_same_thread=False)
            self._connection_pool.put(conn)
    
    def get_connection(self):
        return self._connection_pool.get()
    
    def release_connection(self, conn):
        self._connection_pool.put(conn)
    
    def _initialize_database(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    donor_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    notes TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_recurring BOOLEAN DEFAULT 0,
                    recurring_interval TEXT,
                    next_donation_date TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            default_categories = ['General', 'Project', 'Emergency', 'Other']
            for category in default_categories:
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                    (category,)
                )
            conn.commit()
        finally:
            self.release_connection(conn)
    
    def add_donation(self, donor_name: str, amount: float, category: str, notes: str = None) -> bool:
        """Add a new donation to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO donations (donor_name, amount, category, notes) VALUES (?, ?, ?, ?)",
                    (donor_name, amount, category, notes)
                )
                return True
        except Exception as e:
            print(f"Error adding donation: {str(e)}")
            return False
    
    def get_total_donations(self, category: str = None) -> float:
        """Get total donations, optionally filtered by category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if category:
                    cursor.execute(
                        "SELECT SUM(amount) FROM donations WHERE category = ?",
                        (category,)
                    )
                else:
                    cursor.execute("SELECT SUM(amount) FROM donations")
                result = cursor.fetchone()[0]
                return float(result) if result else 0.0
        except Exception as e:
            print(f"Error getting total donations: {str(e)}")
            return 0.0
    
    def get_recent_donations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent donations with specified limit."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM donations ORDER BY date DESC LIMIT ?",
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting recent donations: {str(e)}")
            return []
    
    def get_category_breakdown(self) -> Dict[str, float]:
        """Get donation totals broken down by category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT category, SUM(amount) FROM donations GROUP BY category"
                )
                return {category: float(amount) for category, amount in cursor.fetchall()}
        except Exception as e:
            print(f"Error getting category breakdown: {str(e)}")
            return {}
    
    def process_nlp_query(self, query: str) -> Dict[str, Any]:
        """Process natural language queries about donations."""
        query = query.lower()
        
        # Pattern matching for different types of queries
        if re.search(r'total|sum|all', query):
            if 'category' in query:
                # Extract category from query
                categories = ['general', 'project', 'emergency', 'other']
                for category in categories:
                    if category in query:
                        return {
                            'type': 'total_category',
                            'amount': self.get_total_donations(category.capitalize()),
                            'category': category.capitalize()
                        }
            return {
                'type': 'total',
                'amount': self.get_total_donations()
            }
        
        elif re.search(r'recent|latest|last', query):
            limit = 5  # Default limit
            # Try to extract number from query
            number_match = re.search(r'\d+', query)
            if number_match:
                limit = min(int(number_match.group()), 20)  # Cap at 20 for reasonable output
            return {
                'type': 'recent',
                'donations': self.get_recent_donations(limit)
            }
        
        elif re.search(r'category|breakdown|distribution', query):
            return {
                'type': 'breakdown',
                'distribution': self.get_category_breakdown()
            }
        
        return {
            'type': 'unknown',
            'message': 'I could not understand your query. Please try asking about total donations, recent donations, or category breakdown.'
        }
    
    def get_donor_names(self) -> List[str]:
        """Get a list of all unique donor names from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT donor_name FROM donations ORDER BY donor_name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting donor names: {str(e)}")
            return []
            
    def get_donor_statistics(self) -> Dict[str, Any]:
        """Get comprehensive donor statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get total number of unique donors
                cursor.execute("SELECT COUNT(DISTINCT donor_name) FROM donations")
                total_donors = cursor.fetchone()[0]
                
                # Get average donation amount
                cursor.execute("SELECT AVG(amount) FROM donations")
                avg_donation = cursor.fetchone()[0] or 0.0
                
                # Get donor frequency
                cursor.execute("""
                    SELECT donor_name, COUNT(*) as donation_count, SUM(amount) as total_amount
                    FROM donations
                    GROUP BY donor_name
                    ORDER BY total_amount DESC
                    LIMIT 5
                """)
                top_donors = [{
                    'name': row[0],
                    'donation_count': row[1],
                    'total_amount': row[2]
                } for row in cursor.fetchall()]
                
                return {
                    'total_donors': total_donors,
                    'average_donation': round(avg_donation, 2),
                    'top_donors': top_donors
                }
        except Exception as e:
            print(f"Error getting donor statistics: {str(e)}")
            return {
                'total_donors': 0,
                'average_donation': 0.0,
                'top_donors': []
            }

    def process_nlp_donation(self, text: str) -> Dict[str, Any]:
        """Process natural language donation entries."""
        # Extract amount using regex
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', text)
        if not amount_match:
            return {'success': False, 'message': 'Could not find donation amount in the text.'}
        
        amount = float(amount_match.group(1))
        
        # Extract category
        categories = ['general', 'project', 'emergency', 'other']
        category = 'General'  # Default category
        for cat in categories:
            if cat in text.lower():
                category = cat.capitalize()
                break
        
        # Extract name (assume it's mentioned after 'from' or 'by')
        name_match = re.search(r'(?:from|by)\s+([\w\s]+?)(?:\s+(?:for|to|amount|\$|\d)|$)', text, re.IGNORECASE)
        donor_name = name_match.group(1).strip() if name_match else 'Anonymous'
        
        # Extract notes (anything after 'for' or 'notes')
        notes_match = re.search(r'(?:for|notes:?)\s+([^$\n]+)', text, re.IGNORECASE)
        notes = notes_match.group(1).strip() if notes_match else None
        
        # Add the donation
        success = self.add_donation(donor_name, amount, category, notes)
        
        return {
            'success': success,
            'message': f'Successfully recorded donation of ${amount:.2f} from {donor_name} in {category} category.' if success
                      else 'Failed to record donation. Please try again.',
            'details': {
                'donor_name': donor_name,
                'amount': amount,
                'category': category,
                'notes': notes
            } if success else None
        }
    
    def __init__(self):
        self.db_path = 'donations.db'
        if not os.path.exists(self.db_path):
            self._initialize_database()

    def get_categories(self) -> List[str]:
        """Get all available donation categories."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM categories ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting categories: {str(e)}")
            return ['General', 'Project', 'Emergency', 'Other']