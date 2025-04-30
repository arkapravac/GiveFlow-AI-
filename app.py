import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from chatbot import ChatBot
import os
import pandas as pd
from style import apply_modern_style, create_custom_font, style_text_widget
from PIL import Image, ImageTk

class DonationTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Donation Tracker")
        self.root.geometry("800x600")
        
        # Create splash screen
        self.splash = tk.Toplevel(self.root)
        self.splash.title("")
        self.splash.geometry("800x600")
        self.splash.overrideredirect(True)  # Remove window decorations
        
        # Load and display splash image
        img = Image.open("img.png")
        img = img.resize((800, 600), Image.Resampling.LANCZOS)
        self.splash_img = ImageTk.PhotoImage(img)
        splash_label = tk.Label(self.splash, image=self.splash_img)
        splash_label.pack(fill='both', expand=True)
        
        # Center splash screen
        self.splash.update_idletasks()
        width = self.splash.winfo_width()
        height = self.splash.winfo_height()
        x = (self.splash.winfo_screenwidth() // 2) - (width // 2)
        y = (self.splash.winfo_screenheight() // 2) - (height // 2)
        self.splash.geometry(f"{width}x{height}+{x}+{y}")
        
        # Hide main window initially
        self.root.withdraw()
        
        # Schedule splash screen removal and app initialization
        self.root.after(5000, self._remove_splash)
    
    def _remove_splash(self):
        self.splash.destroy()
        self.root.deiconify()
        self.loading_label = ttk.Label(self.root, text="Initializing application...")
        self.loading_label.pack(expand=True)
        self.root.after(100, self._initialize_app)
    
    def _initialize_app(self):
        # Initialize database in background
        import threading
        db_thread = threading.Thread(target=self.init_database)
        db_thread.start()
        
        # Initialize chatbot
        self.chatbot = ChatBot()
        
        # Apply modern styling
        apply_modern_style(self.root)
        self.custom_fonts = create_custom_font()
        
        # Create main container
        self.main_container = ttk.Notebook(self.root, style='Modern.TNotebook')
        
        # Create tabs
        self.donation_frame = ttk.Frame(self.main_container, style='Modern.TFrame')
        self.chat_frame = ttk.Frame(self.main_container, style='Modern.TFrame')
        self.reports_frame = ttk.Frame(self.main_container, style='Modern.TFrame')
        
        # Remove loading label
        self.loading_label.destroy()
        
        # Setup UI
        self.main_container.pack(expand=True, fill='both', padx=20, pady=10)
        self.main_container.add(self.donation_frame, text='Donations')
        self.main_container.add(self.chat_frame, text='Chat Assistant')
        self.main_container.add(self.reports_frame, text='Reports')
        
        # Setup UI components
        self.setup_donation_ui()
        self.setup_chat_ui()
        self.setup_reports_ui()
    
    def init_database(self):
        # Create database and tables if they don't exist
        with sqlite3.connect('donations.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS donations (
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS donor_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    preferred_category TEXT,
                    total_donations REAL DEFAULT 0,
                    last_donation_date TEXT,
                    notification_preferences TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS donation_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    status TEXT DEFAULT 'active'
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    donor_id INTEGER,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    sent_at TEXT,
                    FOREIGN KEY (donor_id) REFERENCES donor_profiles(id)
                )
            ''')
            conn.commit()
    
    def setup_donation_ui(self):
        # Create canvas for scrollable content
        canvas = tk.Canvas(self.donation_frame)
        canvas.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Add scrollbar to canvas
        scrollbar = ttk.Scrollbar(self.donation_frame, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create main frame inside canvas
        main_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=main_frame, anchor='nw', width=canvas.winfo_width())
        
        # Donation entry form
        entry_frame = ttk.LabelFrame(main_frame, text="New Donation", padding=15, style='Modern.TLabelframe')
        entry_frame.pack(fill='x', padx=20, pady=10)
        
        # Donor Information
        donor_info_frame = ttk.LabelFrame(entry_frame, text="Donor Information", padding=10)
        donor_info_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        # Donor Name
        ttk.Label(donor_info_frame, text="Name:").grid(row=0, column=0, padx=5, pady=3, sticky='e')
        self.donor_name = ttk.Entry(donor_info_frame, style='Modern.TEntry')
        self.donor_name.grid(row=0, column=1, padx=5, pady=3, sticky='ew')
        
        # Donor Email
        ttk.Label(donor_info_frame, text="Email:").grid(row=0, column=2, padx=5, pady=3, sticky='e')
        self.donor_email = ttk.Entry(donor_info_frame, style='Modern.TEntry')
        self.donor_email.grid(row=0, column=3, padx=5, pady=3, sticky='ew')
        
        # Donor Phone
        ttk.Label(donor_info_frame, text="Phone:").grid(row=1, column=0, padx=5, pady=3, sticky='e')
        self.donor_phone = ttk.Entry(donor_info_frame, style='Modern.TEntry')
        self.donor_phone.grid(row=1, column=1, padx=5, pady=3, sticky='ew')
        
        # Donor Address
        ttk.Label(donor_info_frame, text="Address:").grid(row=1, column=2, padx=5, pady=3, sticky='e')
        self.donor_address = ttk.Entry(donor_info_frame, style='Modern.TEntry')
        self.donor_address.grid(row=1, column=3, padx=5, pady=3, sticky='ew')
        
        # Donation Details
        donation_details_frame = ttk.LabelFrame(entry_frame, text="Donation Details", padding=10)
        donation_details_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        # Amount
        ttk.Label(donation_details_frame, text="Amount:").grid(row=0, column=0, padx=5, pady=3, sticky='e')
        self.amount = ttk.Entry(donation_details_frame, style='Modern.TEntry')
        self.amount.grid(row=0, column=1, padx=5, pady=3, sticky='ew')
        
        # Category
        ttk.Label(donation_details_frame, text="Category:").grid(row=0, column=2, padx=5, pady=3, sticky='e')
        self.category = ttk.Combobox(donation_details_frame, values=['General', 'Project', 'Emergency', 'Other'], style='Modern.TCombobox')
        self.category.grid(row=0, column=3, padx=5, pady=3, sticky='ew')
        
        # Recurring Donation
        self.is_recurring = tk.BooleanVar()
        ttk.Checkbutton(donation_details_frame, text="Recurring Donation", variable=self.is_recurring, command=self.toggle_recurring_options).grid(row=1, column=0, columnspan=2, padx=5, pady=3, sticky='w')
        
        # Recurring Options Frame (initially hidden)
        self.recurring_frame = ttk.Frame(donation_details_frame)
        self.recurring_frame.grid(row=2, column=0, columnspan=4, sticky='ew')
        self.recurring_frame.grid_remove()
        
        # Interval
        ttk.Label(self.recurring_frame, text="Interval:").grid(row=0, column=0, padx=5, pady=3, sticky='e')
        self.recurring_interval = ttk.Combobox(self.recurring_frame, values=['Weekly', 'Monthly', 'Quarterly', 'Yearly'], style='Modern.TCombobox')
        self.recurring_interval.grid(row=0, column=1, padx=5, pady=3, sticky='ew')
        
        # Notes
        ttk.Label(entry_frame, text="Notes:").grid(row=2, column=0, padx=10, pady=8, sticky='ne')
        self.notes = tk.Text(entry_frame, height=3, width=30)
        self.notes.grid(row=2, column=1, padx=10, pady=8, sticky='ew')
        style_text_widget(self.notes)
        
        # Submit button with improved visibility
        submit_btn = ttk.Button(entry_frame, text="Submit Donation", command=self.submit_donation, style='Modern.TButton')
        submit_btn.grid(row=4, column=0, columnspan=2, pady=15, sticky='ew')
        submit_btn.configure(padding=(20, 10))  # Increase button size
        
        # Configure grid columns
        entry_frame.columnconfigure(1, weight=1)
        
        # Configure canvas scrolling
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        main_frame.bind('<Configure>', configure_scroll)
        
        # Configure canvas resize
        def on_canvas_configure(event):
            canvas.itemconfig(canvas.find_withtag('all')[0], width=event.width-40)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Recent donations list
        list_frame = ttk.LabelFrame(self.donation_frame, text="Recent Donations", padding=15, style='Modern.TLabelframe')
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Treeview for donations
        self.donation_tree = ttk.Treeview(list_frame, columns=('Donor', 'Amount', 'Category', 'Date', 'Notes'),
                                         show='headings', style='Modern.Treeview')
        self.donation_tree.heading('Donor', text='Donor')
        self.donation_tree.heading('Amount', text='Amount')
        self.donation_tree.heading('Category', text='Category')
        self.donation_tree.heading('Date', text='Date')
        self.donation_tree.heading('Notes', text='Notes')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.donation_tree.yview)
        self.donation_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.donation_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Add Delete button
        delete_btn = ttk.Button(list_frame, text="Delete Selected", command=self.delete_donation, style='Modern.TButton')
        delete_btn.pack(pady=10)
        
        # Add right-click menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_donation)
        self.donation_tree.bind('<Button-3>', self.show_context_menu)
    
    def setup_chat_ui(self):
        # Chat interface
        chat_container = ttk.Frame(self.chat_frame, style='Modern.TFrame')
        chat_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.chat_history = tk.Text(chat_container, wrap=tk.WORD, state='disabled')
        style_text_widget(self.chat_history)
        self.chat_history.pack(fill='both', expand=True, pady=(0, 10))
        
        # Message entry
        entry_frame = ttk.Frame(chat_container, style='Modern.TFrame')
        entry_frame.pack(fill='x')
        
        self.message_entry = ttk.Entry(entry_frame, style='Modern.TEntry')
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        send_btn = ttk.Button(entry_frame, text="Send", command=self.send_message, style='Modern.TButton')
        send_btn.pack(side='right')
        
        # Bind Enter key to send message
        self.message_entry.bind('<Return>', lambda e: self.send_message())
    
    def setup_reports_ui(self):
        # Reports interface
        controls_frame = ttk.Frame(self.reports_frame, style='Modern.TFrame')
        controls_frame.pack(fill='x', padx=20, pady=10)
        
        # Filters frame
        filters_frame = ttk.LabelFrame(controls_frame, text="Filters", padding=10)
        filters_frame.pack(fill='x', padx=5, pady=5)
        
        # Date range
        ttk.Label(filters_frame, text="Date Range:").grid(row=0, column=0, padx=5, pady=3)
        self.date_range = ttk.Combobox(filters_frame, values=['Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'This Year', 'All Time'], style='Modern.TCombobox')
        self.date_range.grid(row=0, column=1, padx=5, pady=3)
        self.date_range.set('All Time')
        
        # Category filter
        ttk.Label(filters_frame, text="Category:").grid(row=0, column=2, padx=5, pady=3)
        self.category_filter = ttk.Combobox(filters_frame, values=['All Categories', 'General', 'Project', 'Emergency', 'Other'], style='Modern.TCombobox')
        self.category_filter.grid(row=0, column=3, padx=5, pady=3)
        self.category_filter.set('All Categories')
        
        # Donor filter
        ttk.Label(filters_frame, text="Donor:").grid(row=0, column=4, padx=5, pady=3)
        self.donor_filter = ttk.Entry(filters_frame, style='Modern.TEntry')
        self.donor_filter.grid(row=0, column=5, padx=5, pady=3)
        
        # Buttons frame
        button_frame = ttk.Frame(controls_frame, style='Modern.TFrame')
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Generate Report", command=self.generate_report, style='Modern.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Export to Excel", command=self.export_to_excel, style='Modern.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Donor Analytics", command=self.show_donor_analytics, style='Modern.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Donation Trends", command=self.show_donation_trends, style='Modern.TButton').pack(side='left', padx=5)
        
        # Create notebook for different views
        self.report_notebook = ttk.Notebook(self.reports_frame, style='Modern.TNotebook')
        self.report_notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.report_notebook)
        self.report_notebook.add(self.summary_frame, text='Summary')
        
        self.report_text = tk.Text(self.summary_frame, wrap=tk.WORD, state='disabled')
        style_text_widget(self.report_text)
        self.report_text.pack(fill='both', expand=True)
        
        # Trends tab
        self.trends_frame = ttk.Frame(self.report_notebook)
        self.report_notebook.add(self.trends_frame, text='Trends')
        
        # Analytics tab
        self.analytics_frame = ttk.Frame(self.report_notebook)
        self.report_notebook.add(self.analytics_frame, text='Analytics')
    
    def toggle_recurring_options(self):
        if self.is_recurring.get():
            self.recurring_frame.grid()
        else:
            self.recurring_frame.grid_remove()

    def submit_donation(self):
        try:
            # Get donor information
            donor = self.donor_name.get()
            email = self.donor_email.get()
            phone = self.donor_phone.get()
            address = self.donor_address.get()
            
            # Get donation details
            amount = float(self.amount.get())
            category = self.category.get()
            notes = self.notes.get('1.0', 'end-1c')
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get recurring donation information
            is_recurring = self.is_recurring.get()
            recurring_interval = self.recurring_interval.get() if is_recurring else None
            
            # Validate required fields
            if not donor or not amount or not category:
                messagebox.showerror("Error", "Please fill in all required fields")
                return
            
            # Validate recurring donation fields
            if is_recurring and not recurring_interval:
                messagebox.showerror("Error", "Please select a recurring interval")
                return
            
            # Calculate next donation date for recurring donations
            next_donation_date = None
            if is_recurring:
                next_date = datetime.now()
                if recurring_interval == 'Weekly':
                    next_date = next_date.replace(day=next_date.day + 7)
                elif recurring_interval == 'Monthly':
                    if next_date.month == 12:
                        next_date = next_date.replace(year=next_date.year + 1, month=1)
                    else:
                        next_date = next_date.replace(month=next_date.month + 1)
                elif recurring_interval == 'Quarterly':
                    if next_date.month > 9:
                        next_date = next_date.replace(year=next_date.year + 1, month=(next_date.month + 3) % 12)
                    else:
                        next_date = next_date.replace(month=next_date.month + 3)
                elif recurring_interval == 'Yearly':
                    next_date = next_date.replace(year=next_date.year + 1)
                next_donation_date = next_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Save to database
            with sqlite3.connect('donations.db') as conn:
                cursor = conn.cursor()
                
                # Update or create donor profile
                cursor.execute('''
                    INSERT OR REPLACE INTO donor_profiles (name, email, phone, address, preferred_category, last_donation_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (donor, email, phone, address, category, date))
                
                # Get donor_id for the notification
                donor_id = cursor.lastrowid
                
                # Insert donation with next_donation_date
                cursor.execute('''
                    INSERT INTO donations (donor_name, amount, category, date, notes, is_recurring, recurring_interval, next_donation_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (donor, amount, category, date, notes, is_recurring, recurring_interval, next_donation_date))
                
                # Create notification for large donations
                if amount >= 1000:  # Threshold for significant donations
                    cursor.execute('''
                        INSERT INTO email_notifications (donor_id, type, message, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (donor_id, 'large_donation', f'Large donation received: ${amount:.2f} from {donor}', date))
                
                conn.commit()
            
            # Clear form
            self.donor_name.delete(0, 'end')
            self.donor_email.delete(0, 'end')
            self.donor_phone.delete(0, 'end')
            self.donor_address.delete(0, 'end')
            self.amount.delete(0, 'end')
            self.category.set('')
            self.notes.delete('1.0', 'end')
            self.is_recurring.set(False)
            self.recurring_interval.set('')
            self.toggle_recurring_options()
            
            # Update donation list
            self.update_donation_list()
            
            messagebox.showinfo("Success", "Donation recorded successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def update_donation_list(self):
        # Clear current items
        for item in self.donation_tree.get_children():
            self.donation_tree.delete(item)
        
        # Fetch and display recent donations
        with sqlite3.connect('donations.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT donor_name, amount, category, date, notes
                FROM donations
                ORDER BY date DESC
                LIMIT 50
            ''')
            for row in cursor.fetchall():
                self.donation_tree.insert('', 'end', values=row)
    
    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Clear message entry
        self.message_entry.delete(0, 'end')
        
        # Add user message to chat history
        self.chat_history.configure(state='normal')
        self.chat_history.insert('end', f"You: {message}\n")
        
        # Get bot response
        response = self.chatbot.get_response(message)
        
        # Add bot response to chat history
        self.chat_history.insert('end', f"Assistant: {response}\n\n")
        self.chat_history.configure(state='disabled')
        self.chat_history.see('end')
        
        # Save chat history to database
        with sqlite3.connect('donations.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (user_message, bot_response, timestamp)
                VALUES (?, ?, ?)
            ''', (message, response, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
    
    def generate_report(self):
        try:
            with sqlite3.connect('donations.db') as conn:
                cursor = conn.cursor()
                
                # Get total donations
                cursor.execute("SELECT COUNT(*), SUM(amount) FROM donations")
                count, total = cursor.fetchone()
                
                # Get category breakdown
                cursor.execute('''
                    SELECT category, COUNT(*), SUM(amount)
                    FROM donations
                    GROUP BY category
                ''')
                categories = cursor.fetchall()
                
                # Generate report text
                report = f"Donation Summary Report\n"
                report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                report += f"Total Donations: {count if count else 0}\n"
                total_amount = float(total) if total else 0.00
                report += f"Total Amount: ${total_amount:.2f}\n\n"
                report += "Category Breakdown:\n"
                
                for category, cat_count, cat_total in categories:
                    cat_total = float(cat_total) if cat_total else 0.00
                    report += f"{category}:\n"
                    report += f"  Count: {cat_count}\n"
                    report += f"  Total: ${cat_total:.2f}\n"
                
                # Update report text widget
                self.report_text.configure(state='normal')
                self.report_text.delete('1.0', 'end')
                self.report_text.insert('1.0', report)
                self.report_text.configure(state='disabled')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
    
    def show_donor_analytics(self):
        try:
            with sqlite3.connect('donations.db') as conn:
                cursor = conn.cursor()
                
                # Get donor statistics
                cursor.execute('''
                    SELECT 
                        donor_name,
                        COUNT(*) as donation_count,
                        SUM(amount) as total_amount,
                        AVG(amount) as avg_amount,
                        MAX(date) as last_donation
                    FROM donations
                    GROUP BY donor_name
                    ORDER BY total_amount DESC
                ''')
                donor_stats = cursor.fetchall()
                
                # Generate analytics report
                report = "Donor Analytics Report\n\n"
                report += "Top Donors:\n"
                
                for donor, count, total, avg, last_date in donor_stats:
                    report += f"\nDonor: {donor}\n"
                    report += f"Total Donations: {count}\n"
                    report += f"Total Amount: ${total:.2f}\n"
                    report += f"Average Donation: ${avg:.2f}\n"
                    report += f"Last Donation: {last_date}\n"
                
                # Show in analytics tab
                analytics_text = tk.Text(self.analytics_frame, wrap=tk.WORD)
                style_text_widget(analytics_text)
                analytics_text.pack(fill='both', expand=True)
                analytics_text.insert('1.0', report)
                analytics_text.configure(state='disabled')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate donor analytics: {str(e)}")
    
    def show_donation_trends(self):
        try:
            with sqlite3.connect('donations.db') as conn:
                cursor = conn.cursor()
                
                # Get monthly trends
                cursor.execute('''
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        COUNT(*) as donation_count,
                        SUM(amount) as total_amount,
                        category
                    FROM donations
                    GROUP BY month, category
                    ORDER BY month DESC
                ''')
                trends = cursor.fetchall()
                
                # Generate trends report
                report = "Donation Trends Report\n\n"
                report += "Monthly Breakdown:\n"
                
                current_month = None
                for month, count, total, category in trends:
                    if month != current_month:
                        current_month = month
                        report += f"\n{month}:\n"
                    report += f"  {category}: ${total:.2f} ({count} donations)\n"
                
                # Show in trends tab
                trends_text = tk.Text(self.trends_frame, wrap=tk.WORD)
                style_text_widget(trends_text)
                trends_text.pack(fill='both', expand=True)
                trends_text.insert('1.0', report)
                trends_text.configure(state='disabled')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate donation trends: {str(e)}")
    
    def export_to_excel(self):
        try:
            with sqlite3.connect('donations.db') as conn:
                # Create a pandas DataFrame from the donations table
                df = pd.read_sql_query('''
                    SELECT donor_name as 'Donor Name',
                           amount as 'Amount',
                           category as 'Category',
                           date as 'Date',
                           notes as 'Notes'
                    FROM donations
                    ORDER BY date DESC
                ''', conn)
                
                # Convert date column to datetime
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Calculate summary statistics
                total_donations = df['Amount'].sum()
                total_count = len(df)
                category_summary = df.groupby('Category').agg({
                    'Amount': ['count', 'sum']
                }).round(2)
                category_summary.columns = ['Count', 'Total Amount']
                
                # Create visualizations
                import matplotlib.pyplot as plt
                import io
                
                # 1. Category Distribution Pie Chart
                plt.figure(figsize=(10, 6))
                plt.pie(category_summary['Total Amount'], labels=category_summary.index, autopct='%1.1f%%')
                plt.title('Donation Distribution by Category')
                category_pie = io.BytesIO()
                plt.savefig(category_pie)
                plt.close()
                
                # 2. Monthly Trends Line Graph
                monthly_data = df.groupby(df['Date'].dt.to_period('M')).agg({
                    'Amount': 'sum'
                }).reset_index()
                monthly_data['Date'] = monthly_data['Date'].astype(str)
                
                plt.figure(figsize=(12, 6))
                plt.plot(monthly_data['Date'], monthly_data['Amount'], marker='o')
                plt.title('Monthly Donation Trends')
                plt.xticks(rotation=45)
                plt.tight_layout()
                trends_line = io.BytesIO()
                plt.savefig(trends_line)
                plt.close()
                
                # 3. Top Donors Bar Chart
                top_donors = df.groupby('Donor Name')['Amount'].sum().nlargest(10)
                
                plt.figure(figsize=(12, 6))
                plt.bar(top_donors.index, top_donors.values)
                plt.title('Top 10 Donors')
                plt.xticks(rotation=45)
                plt.tight_layout()
                donors_bar = io.BytesIO()
                plt.savefig(donors_bar)
                plt.close()
                
                # Get current timestamp for filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'donation_report_{timestamp}.xlsx'
                
                # Create Excel writer object
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    # Write main donation data
                    df.to_excel(writer, sheet_name='Donations', index=False)
                    
                    # Write summary sheet
                    summary_df = pd.DataFrame({
                        'Metric': ['Total Donations', 'Total Amount'],
                        'Value': [total_count, f'${total_donations:.2f}']
                    })
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Write category breakdown
                    category_summary.to_excel(writer, sheet_name='Category Breakdown')
                    
                    # Add visualizations to the workbook
                    workbook = writer.book
                    
                    # Add graphs worksheet
                    graphs_sheet = workbook.create_sheet('Graphs')
                    
                    # Insert the charts
                    from openpyxl.drawing.image import Image
                    
                    # Category Distribution Pie Chart
                    img_pie = Image(category_pie)
                    graphs_sheet.add_image(img_pie, 'A1')
                    
                    # Monthly Trends Line Graph
                    img_line = Image(trends_line)
                    graphs_sheet.add_image(img_line, 'A20')
                    
                    # Top Donors Bar Chart
                    img_bar = Image(donors_bar)
                    graphs_sheet.add_image(img_bar, 'A40')
                    
                    # Auto-adjust column widths
                    for sheet_name in writer.sheets:
                        worksheet = writer.sheets[sheet_name]
                        if sheet_name != 'Graphs':  # Skip graphs sheet
                            for column in worksheet.columns:
                                max_length = 0
                                column = [cell for cell in column]
                                for cell in column:
                                    try:
                                        if len(str(cell.value)) > max_length:
                                            max_length = len(str(cell.value))
                                    except:
                                        pass
                                adjusted_width = (max_length + 2)
                                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
                
                messagebox.showinfo("Success", f"Report exported successfully as '{filename}'")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {str(e)}")
    
    def run(self):
        # Start the application
        self.root.mainloop()

    def delete_donation(self):
        selected_items = self.donation_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a donation to delete.")
            return
            
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected donation(s)?"):
            return
            
        try:
            with sqlite3.connect('donations.db') as conn:
                cursor = conn.cursor()
                for item in selected_items:
                    # Get the date from the selected item
                    values = self.donation_tree.item(item)['values']
                    date = values[3]  # Date is the fourth column
                    
                    # Delete from database
                    cursor.execute('DELETE FROM donations WHERE date = ?', (date,))
                    
                    # Remove from treeview
                    self.donation_tree.delete(item)
                    
                conn.commit()
            messagebox.showinfo("Success", "Selected donation(s) deleted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete donation(s): {str(e)}")
            
    def show_context_menu(self, event):
        # Show context menu on right-click
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

if __name__ == "__main__":
    app = DonationTracker()
    app.run()
    
    def main():
        print("Welcome to the Donation Management System!")
        print("Type 'exit' to quit the application.")
        
        chatbot = ChatBot()
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("\nThank you for using the Donation Management System. Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = chatbot.get_response(user_input)
                print(f"\nAssistant: {response}")
                
            except KeyboardInterrupt:
                print("\n\nExiting the application...")
                break
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")
                print("Please try again.")
    
    if __name__ == '__main__':
        main()