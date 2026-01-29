import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import random
import re  # For email validation
from datetime import datetime, date
from database_connection import DatabaseConnection
from sql_runner import SQLRunner

# --- Theme Configuration ---
COLOR_PRIMARY = "#004085"     # Dark Blue
COLOR_SECONDARY = "#343a40"   # Dark Gray
COLOR_BG = "#f8f9fa"          # Light Gray
COLOR_WHITE = "#ffffff"
FONT_HEADER = ("Helvetica", 16, "bold")
FONT_NORMAL = ("Helvetica", 10)
FONT_BOLD = ("Helvetica", 10, "bold")

class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("Welcome - Flight Reservation System")
        self.root.geometry("450x500")
        self.root.configure(bg=COLOR_BG)

        self.db = DatabaseConnection()
        self.db.connect() 

        self.create_widgets()
        
        # Fix macOS focus issues
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())

    def create_widgets(self):
        # Title
        tk.Label(self.root, text="Flight Reservation System", font=("Helvetica", 18, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(pady=20)

        # Tab Control
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Login Tab
        self.tab_login = tk.Frame(self.notebook, bg=COLOR_WHITE)
        self.notebook.add(self.tab_login, text="   Login   ")
        self.build_login_tab()

        # Register Tab
        self.tab_register = tk.Frame(self.notebook, bg=COLOR_WHITE)
        self.notebook.add(self.tab_register, text="   Register   ")
        self.build_register_tab()

    def build_login_tab(self):
        frame = tk.Frame(self.tab_login, bg=COLOR_WHITE, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Username", font=FONT_BOLD, bg=COLOR_WHITE).pack(anchor="w")
        self.entry_user = ttk.Entry(frame, width=30)
        self.entry_user.pack(pady=5, fill=tk.X)

        tk.Label(frame, text="Password", font=FONT_BOLD, bg=COLOR_WHITE).pack(anchor="w", pady=(10, 0))
        self.entry_pass = ttk.Entry(frame, width=30, show="*")
        self.entry_pass.pack(pady=5, fill=tk.X)

        btn = ttk.Button(frame, text="Login", command=self.do_login)
        btn.pack(pady=20, fill=tk.X)

    def build_register_tab(self):
        frame = tk.Frame(self.tab_register, bg=COLOR_WHITE, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="New Username", font=FONT_BOLD, bg=COLOR_WHITE).pack(anchor="w")
        self.reg_user = ttk.Entry(frame)
        self.reg_user.pack(pady=5, fill=tk.X)

        tk.Label(frame, text="New Password", font=FONT_BOLD, bg=COLOR_WHITE).pack(anchor="w", pady=(10, 0))
        self.reg_pass = ttk.Entry(frame, show="*")
        self.reg_pass.pack(pady=5, fill=tk.X)

        tk.Label(frame, text="Email", font=FONT_BOLD, bg=COLOR_WHITE).pack(anchor="w", pady=(10, 0))
        self.reg_email = ttk.Entry(frame)
        self.reg_email.pack(pady=5, fill=tk.X)

        btn = ttk.Button(frame, text="Register", command=self.do_register)
        btn.pack(pady=20, fill=tk.X)

    def do_login(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()

        if not user or not pwd:
            messagebox.showwarning("Input Error", "Please enter username and password.")
            return

        try:
            # Call SP_AuthenticateUser
            # DECLARE variables for output parameters
            query = """
            DECLARE @uid INT, @role VARCHAR(20), @pid INT;
            EXEC SP_AuthenticateUser ?, ?, @uid OUTPUT, @role OUTPUT, @pid OUTPUT;
            SELECT @uid, @role, @pid;
            """
            data, msg = self.db.fetch_results(query, (user, pwd))
            
            if data and data[1] and data[1][0][0]:
                # Login Successful
                # user_id = data[1][0][0]
                # role = data[1][0][1]
                self.root.destroy()
                self.on_success()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")
        except Exception as e:
             messagebox.showerror("Login Error", str(e))

    def do_register(self):
        user = self.reg_user.get().strip()
        pwd = self.reg_pass.get().strip()
        email = self.reg_email.get().strip()

        if not user or not pwd or not email:
            messagebox.showwarning("Input Error", "All fields are required.")
            return
            
        # Email Validation: alphanumeric, @, . only + must contain @ and .
        if not re.match(r"^[a-zA-Z0-9.@]+$", email):
            messagebox.showerror("Validation Error", "Email can only contain letters, numbers, '.' and '@'.")
            return
        if "@" not in email or "." not in email:
            messagebox.showerror("Validation Error", "Email must contain '@' and '.'.")
            return
            
        try:
            # Call SP_RegisterUser
            # Checks for duplicate username/email handles inside the SP (RAISERROR)
            query = """
            DECLARE @new_id INT;
            EXEC SP_RegisterUser ?, ?, ?, 'Customer', NULL, @new_id OUTPUT;
            SELECT @new_id;
            """
            
            # Note: SP raises error if user exists, fetch_results catches it in msg
            data, msg = self.db.fetch_results(query, (user, pwd, email))
            
            if data and data[1]:
                messagebox.showinfo("Success", "Registration Successful! Please Login.")
                self.notebook.select(self.tab_login) 
            else:
                # If msg contains error from RAISERROR (e.g. Username exists), show it
                if "Username already exists" in msg:
                    messagebox.showerror("Error", "Username already exists.")
                elif "Email already registered" in msg:
                    messagebox.showerror("Error", "Email already registered.")
                else:
                    messagebox.showerror("Registration Failed", f"Error: {msg}")

        except Exception as e:
            messagebox.showerror("System Error", str(e))


class DatabaseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Flight Reservation System")
        self.root.geometry("1100x750")
        self.root.configure(bg=COLOR_BG)

        self.db = DatabaseConnection()
        self.runner = SQLRunner(self.db)
        self.project_dir = os.path.dirname(os.path.abspath(__file__))

        # Styles
        self.setup_styles()
        
        # Connect
        self.db.connect()
        self.create_widgets()
        
        # Load initial data
        self.refresh_flights()
        self.refresh_bookings()
        
        # Fix macOS focus issues - bind click to all interactive widgets
        self.fix_macos_focus()
    
    def fix_macos_focus(self):
        """Fix macOS Tkinter focus issues"""
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # General formatting
        style.configure("TFrame", background=COLOR_BG)
        style.configure("TLabel", background=COLOR_BG, font=FONT_NORMAL)
        
        # Button Styles - Darker
        style.configure("TButton", background=COLOR_PRIMARY, foreground=COLOR_WHITE, font=FONT_BOLD, borderwidth=0)
        style.map("TButton", 
                  background=[("active", "#002752"), ("pressed", "#002752")], 
                  foreground=[("active", COLOR_WHITE)])
        
        # Secondary Button Style
        style.configure("Secondary.TButton", background=COLOR_SECONDARY, foreground=COLOR_WHITE, font=FONT_BOLD)
        style.map("Secondary.TButton", background=[("active", "#23272b")])

        # Treeview
        style.configure("Treeview", rowheight=25, font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#e9ecef")

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg=COLOR_PRIMARY, height=60)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="✈  Flight Reservation System", font=("Helvetica", 20, "bold"), 
                 bg=COLOR_PRIMARY, fg=COLOR_WHITE).pack(pady=15)

        # Main Tab Control
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Tab 1: Flights
        self.tab_flights = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_flights, text="  Search Flights  ")
        self.build_flights_tab()

        # Tab 2: My Bookings
        self.tab_bookings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_bookings, text="  My Bookings  ")
        self.build_bookings_tab()

        # Tab 3: Analytics
        self.tab_analytics = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analytics, text="  Analytics  ")
        self.build_analytics_tab()

        # Tab 4: Admin
        self.tab_admin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text="  Admin & Setup  ")
        self.build_admin_tab()
        
    def build_flights_tab(self):
        # Search Panel using SP_SearchFlights
        search_frame = ttk.LabelFrame(self.tab_flights, text="Search Flights (SP_SearchFlights)", padding="10")
        search_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Row 1: Departure and Arrival
        row1 = ttk.Frame(search_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="From:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_departure = ttk.Combobox(row1, width=20, state="readonly")
        self.combo_departure.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1, text="To:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_arrival = ttk.Combobox(row1, width=20, state="readonly")
        self.combo_arrival.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1, text="Date (YYYY-MM-DD):", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_travel_date = ttk.Entry(row1, width=15)
        self.entry_travel_date.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1, text="Class:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_class = ttk.Combobox(row1, values=["Any", "Economy", "Business", "First Class"], width=12, state="readonly")
        self.combo_class.set("Any")
        self.combo_class.pack(side=tk.LEFT, padx=(0, 20))
        
        btn_search = ttk.Button(row1, text="🔍 Search", style="TButton", command=self.search_flights)
        btn_search.pack(side=tk.LEFT, padx=5)
        
        btn_clear = ttk.Button(row1, text="Clear", style="Secondary.TButton", command=self.clear_search)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        # Populate dropdowns with airports
        self.populate_airport_combos()
        
        # Action frame
        action_frame = ttk.Frame(self.tab_flights, padding="15")
        action_frame.pack(fill=tk.X)
        
        ttk.Label(action_frame, text="Available Flights", font=FONT_HEADER).pack(side=tk.LEFT)
        
        btn_refresh = ttk.Button(action_frame, text="↻ Show All Flights", style="Secondary.TButton", command=self.refresh_flights)
        btn_refresh.pack(side=tk.RIGHT, padx=5)
        
        btn_book = ttk.Button(action_frame, text="✓ Book Selected Flight", style="TButton", command=self.open_booking_window)
        btn_book.pack(side=tk.RIGHT, padx=5)

        # Treeview
        columns = ("ID", "Airline", "Flight No", "Origin", "Dest", "Departure", "Price", "Seats", "Status")
        self.flight_tree = ttk.Treeview(self.tab_flights, columns=columns, show="headings", height=12)
        
        widths = [50, 180, 80, 120, 120, 160, 80, 60, 80]
        for i, col in enumerate(columns):
            self.flight_tree.heading(col, text=col)
            self.flight_tree.column(col, width=widths[i])
            
        self.flight_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Double-click to book a flight
        self.flight_tree.bind("<Double-1>", self.on_flight_double_click)
        
        scrollbar = ttk.Scrollbar(self.tab_flights, orient=tk.VERTICAL, command=self.flight_tree.yview)
        self.flight_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def on_flight_double_click(self, event):
        """Handle double-click on flight to open booking window"""
        selected = self.flight_tree.selection()
        if selected:
            self.open_booking_window()
    
    def populate_airport_combos(self):
        """Populate departure and arrival dropdowns with airports"""
        query = "SELECT airport_id, city + ' (' + airport_code + ')' AS display FROM AIRPORTS WHERE status = 'Operational' ORDER BY city"
        data, msg = self.db.fetch_results(query)
        if data and data[1]:
            self.airport_list = [(row[0], row[1]) for row in data[1]]
            display_values = [row[1] for row in data[1]]
            self.combo_departure['values'] = display_values
            self.combo_arrival['values'] = display_values
    
    def get_airport_id(self, display_value):
        """Get airport_id from display value"""
        for aid, display in self.airport_list:
            if display == display_value:
                return aid
        return None
    
    def search_flights(self):
        """Search flights using SP_SearchFlights stored procedure"""
        dep_display = self.combo_departure.get()
        arr_display = self.combo_arrival.get()
        travel_date = self.entry_travel_date.get().strip()
        class_type = self.combo_class.get()
        
        if not dep_display or not arr_display or not travel_date:
            messagebox.showwarning("Input Required", "Please select departure, arrival airports and travel date.")
            return
        
        # Validation: Origin and Destination must be different
        if dep_display == arr_display:
            messagebox.showerror("Invalid Selection", "Origin and Destination cannot be the same airport.\nPlease select different airports.")
            return
        
        # Validation: Date must not be in the past
        try:
            travel_date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()
            today = date.today()
            if travel_date_obj < today:
                messagebox.showerror("Invalid Date", f"The date {travel_date} has already passed.\nPlease enter a future date (today is {today}).")
                return
        except ValueError:
            messagebox.showerror("Invalid Date Format", "Please enter date in YYYY-MM-DD format (e.g., 2024-12-30).")
            return
        
        dep_id = self.get_airport_id(dep_display)
        arr_id = self.get_airport_id(arr_display)
        
        if not dep_id or not arr_id:
            messagebox.showerror("Error", "Invalid airport selection.")
            return
        
        # Clear treeview
        for item in self.flight_tree.get_children():
            self.flight_tree.delete(item)
        
        # Call SP_SearchFlights
        try:
            if class_type == "Any":
                query = "EXEC SP_SearchFlights @departure_airport_id=?, @arrival_airport_id=?, @travel_date=?"
                params = (dep_id, arr_id, travel_date)
            else:
                query = "EXEC SP_SearchFlights @departure_airport_id=?, @arrival_airport_id=?, @travel_date=?, @class_type=?"
                params = (dep_id, arr_id, travel_date, class_type)
            
            data, msg = self.db.fetch_results(query, params)
            
            if data and data[1]:
                for row in data[1]:
                    # Columns: flight_id, flight_number, airline_name, airline_code, dep_airport, dep_city, arr_airport, arr_city, dep_time, arr_time, duration, base_price, avail_seats, aircraft, status, gate, class_price
                    display_row = (row[0], row[2], row[1], row[5], row[7], row[8], row[16] if len(row) > 16 else row[11], row[12], row[14])
                    self.flight_tree.insert("", tk.END, values=display_row)
                self.log(f"Search found {len(data[1])} flights.")
            else:
                messagebox.showinfo("No Results", "No flights found for the selected criteria.")
        except Exception as e:
            messagebox.showerror("Search Error", str(e))
    
    def clear_search(self):
        """Clear search filters and show all flights"""
        self.combo_departure.set('')
        self.combo_arrival.set('')
        self.entry_travel_date.delete(0, tk.END)
        self.combo_class.set("Any")
        self.refresh_flights()

    def build_bookings_tab(self):
        ttk.Label(self.tab_bookings, text="Reservation Details (VW_PassengerReservationDetails)", font=FONT_HEADER).pack(pady=15)
        
        # Enhanced columns from the view
        columns = ("ID", "Reference", "Passenger", "Flight", "Airline", "Route", "Seat", "Class", "Status", "Payment", "Amount")
        self.booking_tree = ttk.Treeview(self.tab_bookings, columns=columns, show="headings", height=12)
        
        widths = [40, 80, 120, 70, 100, 140, 50, 70, 80, 70, 80]
        for i, col in enumerate(columns):
            self.booking_tree.heading(col, text=col)
            self.booking_tree.column(col, width=widths[i])
        
        self.booking_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Context Menu
        self.booking_menu = tk.Menu(self.booking_tree, tearoff=0)
        self.booking_menu.add_command(label="Check-In (Get Boarding Pass)", command=self.action_checkin)
        self.booking_menu.add_command(label="Cancel Reservation", command=self.action_cancel)
        self.booking_tree.bind("<Button-3>", self.show_booking_menu) # Right click on Windows/Linux
        self.booking_tree.bind("<Button-2>", self.show_booking_menu) # Right click on Mac
        
        # Action Buttons Frame
        action_frame = ttk.Frame(self.tab_bookings, padding="10")
        action_frame.pack(fill=tk.X)

        btn_refresh = ttk.Button(action_frame, text="Refresh Bookings", style="Secondary.TButton", command=self.refresh_bookings)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        btn_cancel = ttk.Button(action_frame, text="Cancel Reservation", style="TButton", command=self.action_cancel)
        btn_cancel.pack(side=tk.RIGHT, padx=5)

        btn_checkin = ttk.Button(action_frame, text="Check-In", style="TButton", command=self.action_checkin)
        btn_checkin.pack(side=tk.RIGHT, padx=5)

    def show_booking_menu(self, event):
        item = self.booking_tree.identify_row(event.y)
        if item:
            self.booking_tree.selection_set(item)
            self.booking_menu.post(event.x_root, event.y_root)

    def action_checkin(self):
        selected = self.booking_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a reservation to check-in.")
            return
        
        values = self.booking_tree.item(selected[0])['values']
        res_id = values[0]  # ID column
        status = values[8]  # Status column (updated index for new columns)
        
        if status == 'Cancelled':
            messagebox.showerror("Error", "Cannot check-in a cancelled reservation.")
            return

        try:
            # Call SP_CheckInPassenger
            sql = """
            DECLARE @info VARCHAR(MAX);
            EXEC SP_CheckInPassenger ?, @info OUTPUT;
            SELECT @info;
            """
            data, msg = self.db.fetch_results(sql, (res_id,))
            
            if data and data[1] and data[1][0][0]:
                pass_info = data[1][0][0]
                messagebox.showinfo("Boarding Pass", pass_info)
                self.refresh_bookings()
            else:
                 # It might return error via RAISERROR which goes to Exception
                 pass

        except Exception as e:
            # If SP raises error (e.g. not eligible), catch it
            messagebox.showerror("Check-In Failed", str(e))
            
    def action_cancel(self):
        selected = self.booking_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a reservation to cancel.")
            return
        
        values = self.booking_tree.item(selected[0])['values']
        res_id = values[0]  # ID column
        status = values[8]  # Status column (updated index for new columns)
        
        if status == 'Cancelled':
            messagebox.showinfo("Info", "Already cancelled.")
            return

        if not messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel? Refund rules apply."):
            return

        try:
            # Call SP_CancelReservation
            sql = """
            DECLARE @refund DECIMAL(10,2);
            EXEC SP_CancelReservation ?, 'User Requested', @refund OUTPUT;
            SELECT @refund;
            """
            data, msg = self.db.fetch_results(sql, (res_id,))
            
            if data and data[1]:
                refund = data[1][0][0]
                messagebox.showinfo("Cancelled", f"Reservation Cancelled.\nRefund Amount: ${refund}")
                self.refresh_bookings()
                self.refresh_analytics()

        except Exception as e:
             messagebox.showerror("Cancellation Failed", str(e))

    def build_analytics_tab(self):
        # Split into three panes
        paned = tk.PanedWindow(self.tab_analytics, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. Airline Performance
        frame1 = ttk.LabelFrame(paned, text="Airline Performance (VW_AirlinePerformance)", padding=10)
        paned.add(frame1)
        
        columns1 = ("Airline", "Flights", "Passengers", "Occupancy %", "Revenue")
        self.tree_analytics1 = ttk.Treeview(frame1, columns=columns1, show="headings", height=4)
        for col in columns1:
            self.tree_analytics1.heading(col, text=col)
            self.tree_analytics1.column(col, width=120)
        self.tree_analytics1.pack(fill=tk.BOTH, expand=True)

        # 2. Daily Revenue
        frame2 = ttk.LabelFrame(paned, text="Daily Revenue (VW_DailyRevenue)", padding=10)
        paned.add(frame2)
        
        columns2 = ("Date", "Bookings", "Gross Revenue", "Paid Revenue")
        self.tree_analytics2 = ttk.Treeview(frame2, columns=columns2, show="headings", height=4)
        for col in columns2:
            self.tree_analytics2.heading(col, text=col)
            self.tree_analytics2.column(col, width=120)
        self.tree_analytics2.pack(fill=tk.BOTH, expand=True)
        
        # 3. Flight Statistics (NEW - VW_FlightStatistics)
        frame3 = ttk.LabelFrame(paned, text="Flight Statistics (VW_FlightStatistics)", padding=10)
        paned.add(frame3)
        
        columns3 = ("Flight", "Airline", "Departure", "Total Seats", "Available", "Booked", "Occupancy %", "Revenue")
        self.tree_analytics3 = ttk.Treeview(frame3, columns=columns3, show="headings", height=5)
        widths3 = [70, 150, 130, 80, 70, 60, 80, 100]
        for i, col in enumerate(columns3):
            self.tree_analytics3.heading(col, text=col)
            self.tree_analytics3.column(col, width=widths3[i])
        self.tree_analytics3.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        ttk.Button(self.tab_analytics, text="Refresh Analytics", style="Secondary.TButton", command=self.refresh_analytics).pack(pady=5)

    def build_admin_tab(self):
        btn_frame = ttk.Frame(self.tab_admin, padding="20")
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Re-Connect Database", style="Secondary.TButton", command=self.connect_db).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Run All SQL Scripts (Reset DB)", style="Secondary.TButton", command=self.run_all_scripts).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Show Tables Log", style="Secondary.TButton", command=self.show_tables_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update Flight Status", style="Secondary.TButton", command=self.open_update_status_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Show Audit Log", style="Secondary.TButton", command=self.show_audit_log).pack(side=tk.LEFT, padx=5)

        self.log_area = scrolledtext.ScrolledText(self.tab_admin, height=15, font=("Consolas", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    def open_update_status_window(self):
        """Open a window to update flight status (Triggers Audit Log)"""
        top = tk.Toplevel(self.root)
        top.title("Update Flight Status")
        top.geometry("400x300")
        top.configure(bg=COLOR_BG)
        
        tk.Label(top, text="Update Flight Status", font=FONT_HEADER, bg=COLOR_BG).pack(pady=10)
        
        frame = tk.Frame(top, bg=COLOR_WHITE, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(frame, text="Flight ID:", font=FONT_BOLD, bg=COLOR_WHITE).pack(anchor="w")
        entry_fid = ttk.Entry(frame)
        entry_fid.pack(fill=tk.X, pady=5)
        
        tk.Label(frame, text="New Status:", font=FONT_BOLD, bg=COLOR_WHITE).pack(anchor="w", pady=(10,0))
        combo_status = ttk.Combobox(frame, values=["Scheduled", "Boarding", "Departed", "Arrived", "Delayed", "Cancelled"], state="readonly")
        combo_status.pack(fill=tk.X, pady=5)
        combo_status.set("Delayed")
        
        def do_update():
            fid = entry_fid.get().strip()
            status = combo_status.get()
            
            if not fid or not fid.isdigit():
                messagebox.showerror("Error", "Please enter a valid Flight ID.")
                return
                
            try:
                # Call SP_UpdateFlightStatus
                query = "EXEC SP_UpdateFlightStatus @flight_id=?, @new_status=?"
                if self.db.execute_commit(query, (fid, status)):
                    messagebox.showinfo("Success", "Flight Status Updated.\nCheck Audit Log for details.")
                    top.destroy()
                    self.refresh_flights()
                else:
                    messagebox.showerror("Error", "Failed to update status.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        ttk.Button(frame, text="Update Status", style="TButton", command=do_update).pack(pady=20, fill=tk.X)

    # --- Data Operations ---
    def refresh_flights(self):
        for item in self.flight_tree.get_children():
            self.flight_tree.delete(item)
            
        # Using the View VW_AvailableFlights if available, else fallback
        # Let's try to use the view first as it's "Advanced"
        view_query = "SELECT flight_id, airline_name, flight_number, departure_city, arrival_city, departure_datetime, base_price, available_seats, status FROM VW_AvailableFlights ORDER BY departure_datetime"
        data, msg = self.db.fetch_results(view_query)
        
        if not data: # Fallback if View not created yet
             self.log("View VW_AvailableFlights not found, using raw query.")
             query = """
                SELECT F.flight_id, A.airline_name, F.flight_number, 
                    Dep.city, Arr.city, F.departure_datetime, F.base_price, F.available_seats, F.status
                FROM FLIGHTS F
                JOIN AIRLINES A ON F.airline_id = A.airline_id
                JOIN AIRPORTS Dep ON F.departure_airport_id = Dep.airport_id
                JOIN AIRPORTS Arr ON F.arrival_airport_id = Arr.airport_id
                WHERE F.status = 'Scheduled'
                ORDER BY F.departure_datetime
             """
             data, msg = self.db.fetch_results(query)

        if data and data[1]:
            for row in data[1]:
                self.flight_tree.insert("", tk.END, values=list(row))

    def refresh_bookings(self):
        for item in self.booking_tree.get_children():
            self.booking_tree.delete(item)
        
        # Use VW_PassengerReservationDetails view for richer data
        query = """
        SELECT TOP 20 
            reservation_id, 
            booking_reference, 
            passenger_name, 
            flight_number, 
            airline_name,
            departure_city + ' → ' + arrival_city AS route,
            seat_number, 
            class_type,
            reservation_status, 
            payment_status,
            total_price
        FROM VW_PassengerReservationDetails
        ORDER BY booking_date DESC
        """
        data, msg = self.db.fetch_results(query)
        
        if not data:  # Fallback if view doesn't exist
            self.log("View VW_PassengerReservationDetails not found, using raw query.")
            query = """
            SELECT TOP 20 R.reservation_id, R.booking_reference, 
                   P.first_name + ' ' + P.last_name AS passenger_name, 
                   F.flight_number, A.airline_name,
                   Dep.city + ' → ' + Arr.city AS route,
                   R.seat_number, R.class_type, R.reservation_status, R.payment_status, R.total_price
            FROM RESERVATIONS R
            JOIN PASSENGERS P ON R.passenger_id = P.passenger_id
            JOIN FLIGHTS F ON R.flight_id = F.flight_id
            JOIN AIRLINES A ON F.airline_id = A.airline_id
            JOIN AIRPORTS Dep ON F.departure_airport_id = Dep.airport_id
            JOIN AIRPORTS Arr ON F.arrival_airport_id = Arr.airport_id
            ORDER BY R.reservation_id DESC
            """
            data, msg = self.db.fetch_results(query)
        
        if data and data[1]:
            for row in data[1]:
                self.booking_tree.insert("", tk.END, values=list(row))

    def refresh_analytics(self):
        # 1. Airline Performance
        for item in self.tree_analytics1.get_children(): 
            self.tree_analytics1.delete(item)
        q1 = "SELECT airline_name, total_flights, total_passengers, avg_occupancy_rate, total_revenue FROM VW_AirlinePerformance"
        d1, msg1 = self.db.fetch_results(q1)
        if d1 and d1[1]:
            for r in d1[1]: 
                self.tree_analytics1.insert("", tk.END, values=list(r))
            
        # 2. Daily Revenue
        for item in self.tree_analytics2.get_children(): 
            self.tree_analytics2.delete(item)
        q2 = "SELECT booking_date, total_bookings, gross_revenue, paid_revenue FROM VW_DailyRevenue ORDER BY booking_date DESC"
        d2, msg2 = self.db.fetch_results(q2)
        if d2 and d2[1]:
            for r in d2[1]: 
                self.tree_analytics2.insert("", tk.END, values=list(r))
        
        # 3. Flight Statistics (VW_FlightStatistics)
        for item in self.tree_analytics3.get_children(): 
            self.tree_analytics3.delete(item)
        q3 = """
        SELECT flight_number, airline_name, departure_datetime, total_seats, available_seats,
               booked_seats, occupancy_percentage, total_revenue
        FROM VW_FlightStatistics
        ORDER BY departure_datetime DESC
        """
        d3, msg3 = self.db.fetch_results(q3)
        if d3 and d3[1]:
            for r in d3[1]: 
                self.tree_analytics3.insert("", tk.END, values=list(r))

    def open_booking_window(self):
        selected = self.flight_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a flight to book.")
            return
        
        flight_values = self.flight_tree.item(selected[0])['values']
        flight_id = flight_values[0]
        base_price = float(flight_values[6])
        dep_date = flight_values[5] # String or datetime object
        
        top = tk.Toplevel(self.root)
        top.title(f"Book Flight {flight_values[2]}")
        top.geometry("450x700")
        top.configure(bg=COLOR_BG)
        
        tk.Label(top, text="Passenger Details", font=FONT_HEADER, bg=COLOR_BG).pack(pady=10)
        
        entry_frame = tk.Frame(top, bg=COLOR_WHITE, padx=15, pady=15, relief=tk.RAISED)
        entry_frame.pack(fill=tk.X, padx=20)
        
        entries = {}
        fields = ["First Name", "Last Name", "Passport No", "Email", "Phone"]
        
        for field in fields:
            row = tk.Frame(entry_frame, bg=COLOR_WHITE)
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=field, width=12, anchor="w", bg=COLOR_WHITE, font=FONT_BOLD).pack(side=tk.LEFT)
            e = ttk.Entry(row)
            e.pack(side=tk.RIGHT, expand=True, fill=tk.X)
            entries[field] = e

        # Class Selection
        row_class = tk.Frame(entry_frame, bg=COLOR_WHITE)
        row_class.pack(fill=tk.X, pady=5)
        tk.Label(row_class, text="Class", width=12, anchor="w", bg=COLOR_WHITE, font=FONT_BOLD).pack(side=tk.LEFT)
        class_combo = ttk.Combobox(row_class, values=["Economy", "Business", "First Class"], state="readonly")
        class_combo.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        class_combo.set("Economy")

        row_seat = tk.Frame(entry_frame, bg=COLOR_WHITE)
        row_seat.pack(fill=tk.X, pady=5)
        tk.Label(row_seat, text="Seat Pref", width=12, anchor="w", bg=COLOR_WHITE, font=FONT_BOLD).pack(side=tk.LEFT)
        seat_combo = ttk.Combobox(row_seat, values=["1A", "1B", "1C", "2A", "2B", "2C", "3A", "3B"], state="readonly")
        seat_combo.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        seat_combo.set("1A")
        
        # Payment Section (SP_ProcessPayment)
        tk.Label(top, text="Payment Details (SP_ProcessPayment)", font=FONT_HEADER, bg=COLOR_BG).pack(pady=(15, 5))
        
        payment_frame = tk.Frame(top, bg=COLOR_WHITE, padx=15, pady=15, relief=tk.RAISED)
        payment_frame.pack(fill=tk.X, padx=20)
        
        row_pay_method = tk.Frame(payment_frame, bg=COLOR_WHITE)
        row_pay_method.pack(fill=tk.X, pady=5)
        tk.Label(row_pay_method, text="Pay Method", width=12, anchor="w", bg=COLOR_WHITE, font=FONT_BOLD).pack(side=tk.LEFT)
        payment_combo = ttk.Combobox(row_pay_method, values=["Credit Card", "Debit Card", "PayPal", "Bank Transfer"], state="readonly")
        payment_combo.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        payment_combo.set("Credit Card")
        
        row_card = tk.Frame(payment_frame, bg=COLOR_WHITE)
        row_card.pack(fill=tk.X, pady=5)
        tk.Label(row_card, text="Card Last 4", width=12, anchor="w", bg=COLOR_WHITE, font=FONT_BOLD).pack(side=tk.LEFT)
        entry_card_last4 = ttk.Entry(row_card, width=6)
        entry_card_last4.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(row_card, text="(optional, for card payments)", bg=COLOR_WHITE, font=("Helvetica", 8)).pack(side=tk.LEFT)

        # Dynamic Price Label
        lbl_price = tk.Label(top, text=f"Total Price: ${base_price}", font=("Helvetica", 14, "bold"), fg="green", bg=COLOR_BG)
        lbl_price.pack(pady=5)
        
        # Availability Label
        lbl_seats = tk.Label(top, text="Checking availability...", font=("Helvetica", 10), bg=COLOR_BG)
        lbl_seats.pack(pady=5)
        
        def update_price_and_seats(event=None):
            cls = class_combo.get()
            
            # Simple Python Fallback multipliers
            multipliers = {"Economy": 1.0, "Business": 2.5, "First Class": 4.0}
            mult = multipliers.get(cls, 1.0)
            
            # 1. Update Price using DB Function (with fallback)
            try:
                # Try SQL Function first: SELECT dbo.FN_CalculateTicketPrice(...)
                q_price = f"SELECT dbo.FN_CalculateTicketPrice({base_price}, '{cls}', GETDATE(), '{dep_date}')"
                d_price, _ = self.db.fetch_results(q_price)
                if d_price and d_price[1]:
                    new_price = float(d_price[1][0][0])
                else:
                    # Fallback if function returns nothing or doesn't exist
                    new_price = base_price * mult
            except Exception as e:
                # Fallback on any error
                print(f"Pricing Error (using fallback): {e}")
                new_price = base_price * mult
                
            lbl_price.config(text=f"Total Price: ${new_price:.2f}")
            
            # 2. Check Specific Class Availability using DB Function
            try:
                q_seats = f"SELECT dbo.FN_GetAvailableSeatsByClass({flight_id}, '{cls}')"
                d_seats, _ = self.db.fetch_results(q_seats)
                if d_seats and d_seats[1]:
                    seats_avail = d_seats[1][0][0]
                    lbl_seats.config(text=f"Seats Available in {cls}: {seats_avail}", fg="black" if seats_avail > 0 else "red")
                else:
                    lbl_seats.config(text="Availability unknown")
            except:
                lbl_seats.config(text="Availability check failed")
                
            return new_price

        class_combo.bind("<<ComboboxSelected>>", update_price_and_seats)
        # Initial call
        top.after(100, update_price_and_seats)
        
        def validate_and_submit():
            fname = entries["First Name"].get().strip()
            lname = entries["Last Name"].get().strip()
            passport = entries["Passport No"].get().strip()
            email = entries["Email"].get().strip()
            phone = entries["Phone"].get().strip()
            cls = class_combo.get()
            payment_method = payment_combo.get()
            card_last4 = entry_card_last4.get().strip()
            
            # Re-calculate final price securely
            final_price = update_price_and_seats() 
            if final_price is None: final_price = base_price

            # --- Validation Constraints ---
            if not all([fname, lname, passport, email, phone]):
                messagebox.showerror("Validation Error", "All fields are required.")
                return

            if any(char.isdigit() for char in fname) or any(char.isdigit() for char in lname):
                messagebox.showerror("Validation Error", "Name fields cannot contain numbers.")
                return

            # Email Validation
            if not re.match(r"^[a-zA-Z0-9.@]+$", email):
                messagebox.showerror("Validation Error", "Email can only contain letters, numbers, '.' and '@'.")
                return
            if "@" not in email or "." not in email:
                messagebox.showerror("Validation Error", "Email must contain '@' and '.'.")
                return

            phone_clean = phone.replace("+", "").replace("-", "").replace(" ", "")
            if not phone_clean.isdigit():
                 messagebox.showerror("Validation Error", "Phone number must contain only digits.")
                 return
            
            if len(phone_clean) != 11:
                 messagebox.showerror("Validation Error", "Phone number must be exactly 11 digits long.")
                 return

            if not passport.isalnum():
                messagebox.showerror("Validation Error", "Passport Number must be alphanumeric.")
                return
            
            # Card last 4 validation (if provided)
            if card_last4 and (len(card_last4) != 4 or not card_last4.isdigit()):
                messagebox.showerror("Validation Error", "Card last 4 digits must be exactly 4 numbers.")
                return

            # Submit logic
            try:
                # Insert Passenger
                p_query = """
                INSERT INTO PASSENGERS (first_name, last_name, date_of_birth, nationality, passport_number, passport_expiry_date, email, phone_number)
                VALUES (?, ?, '1990-01-01', 'Unknown', ?, '2030-01-01', ?, ?)
                """
                p_params = (fname, lname, passport, email, phone)
                
                if self.db.execute_commit(p_query, p_params):
                    # Fetch ID
                    pid_data, _ = self.db.fetch_results(f"SELECT passenger_id FROM PASSENGERS WHERE passport_number='{passport}'")
                    if pid_data and pid_data[1]:
                        pid = pid_data[1][0][0]
                        
                        # Insert Reservation (with Pending payment status)
                        ref = f"BK{random.randint(10000,99999)}"
                        r_query = """
                        INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, seat_number, class_type, total_price, payment_status)
                        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
                        """
                        r_params = (pid, flight_id, ref, seat_combo.get(), cls, final_price)
                        
                        if self.db.execute_commit(r_query, r_params):
                            # Get reservation ID
                            res_data, _ = self.db.fetch_results(f"SELECT reservation_id FROM RESERVATIONS WHERE booking_reference='{ref}'")
                            if res_data and res_data[1]:
                                res_id = res_data[1][0][0]
                                
                                # Process Payment using SP_ProcessPayment
                                try:
                                    pay_sql = """
                                    DECLARE @payment_id INT;
                                    EXEC SP_ProcessPayment 
                                        @reservation_id=?, 
                                        @payment_method=?, 
                                        @amount=?, 
                                        @card_last_four=?,
                                        @payment_id=@payment_id OUTPUT;
                                    SELECT @payment_id;
                                    """
                                    pay_params = (res_id, payment_method, final_price, card_last4 if card_last4 else None)
                                    pay_data, pay_msg = self.db.fetch_results(pay_sql, pay_params)
                                    
                                    if pay_data and pay_data[1]:
                                        payment_id = pay_data[1][0][0]
                                        messagebox.showinfo("Success", 
                                            f"Ticket Booked & Paid Successfully!\n\n"
                                            f"Booking Ref: {ref}\n"
                                            f"Payment ID: {payment_id}\n"
                                            f"Amount: ${final_price:.2f}\n"
                                            f"Method: {payment_method}\n"
                                            f"Class: {cls}")
                                        top.destroy()
                                        self.refresh_bookings()
                                        self.refresh_analytics()
                                    else:
                                        messagebox.showwarning("Partial Success", 
                                            f"Reservation created but payment processing returned no ID.\n"
                                            f"Booking Ref: {ref}")
                                        top.destroy()
                                        self.refresh_bookings()
                                        
                                except Exception as pay_error:
                                    messagebox.showwarning("Booking Created", 
                                        f"Reservation created but payment failed:\n{pay_error}\n\n"
                                        f"Booking Ref: {ref}\nPlease complete payment later.")
                                    top.destroy()
                                    self.refresh_bookings()
                            else:
                                messagebox.showerror("Error", "Could not retrieve reservation ID.")
                        else:
                            messagebox.showerror("Booking Error", "Failed to create reservation.")
                    else:
                        messagebox.showerror("Error", "Could not retrieve new passenger ID.")
                else:
                    messagebox.showerror("Passenger Error", "Failed to register passenger. \nPassport or Email might already exist.")

            except Exception as e:
                messagebox.showerror("System Error", str(e))

        ttk.Button(top, text="Confirm & Pay", style="TButton", command=validate_and_submit).pack(pady=10)

    # --- Setup Helpers ---
    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def connect_db(self):
        success, msg = self.db.connect()
        self.log(msg)
        if success:
            self.refresh_flights()

    def run_all_scripts(self):
        if messagebox.askyesno("Confirm Reset", "This will WIPE the database and create fresh data. Continue?"):
            self.log("Running all scripts...")
            success, msg = self.runner.run_all_scripts(self.project_dir)
            self.log(msg)
            self.db.connect()
            self.refresh_flights()

    def show_tables_log(self):
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
        data, msg = self.db.fetch_results(query)
        if data and data[1]:
            self.log("Tables found:")
            for r in data[1]:
                self.log(f"- {r[0]}")
    
    def show_audit_log(self):
        query = "SELECT TOP 50 log_id, table_name, operation_type, changed_date, changed_by FROM AUDIT_LOG ORDER BY changed_date DESC"
        data, msg = self.db.fetch_results(query)
        if data and data[1]:
            self.log("--- SYSTEM SECURITY AUDIT LOG ---")
            for r in data[1]:
                self.log(f"[{r[3]}] {r[2]} on {r[1]} by {r[4]}")
        else:
            self.log("No audit records found (or query error).")

def main():
    root = tk.Tk()
    root.withdraw()  # Hide main window initially
    
    def on_login_success():
        login_window.destroy()  # Close login window
        root.deiconify()  # Show main window
        root.lift()
        root.focus_force()
        DatabaseGUI(root)
    
    # Create login window as Toplevel
    login_window = tk.Toplevel(root)
    login_window.protocol("WM_DELETE_WINDOW", root.destroy)  # Close app if login closed
    
    # Force focus on macOS
    login_window.lift()
    login_window.attributes('-topmost', True)
    login_window.after(200, lambda: login_window.attributes('-topmost', False))
    
    LoginWindow(login_window, on_login_success)
    
    root.mainloop()

if __name__ == "__main__":
    main()
