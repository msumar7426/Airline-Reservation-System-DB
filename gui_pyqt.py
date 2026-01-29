import sys
import random
import re
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QFrame, QHeaderView, QTextEdit,
    QDialog, QFormLayout, QDialogButtonBox, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

from database_connection import DatabaseConnection
from sql_runner import SQLRunner
import os

# --- Theme Configuration ---
COLOR_PRIMARY = "#004085"
COLOR_SECONDARY = "#343a40"
COLOR_BG = "#f8f9fa"
COLOR_WHITE = "#ffffff"


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.db.connect()
        self.logged_in = False
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Flight Reservation System - Login")
        self.setFixedSize(400, 350)
        self.setStyleSheet(f"background-color: {COLOR_BG};")
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("✈ Flight Reservation System")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY}; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self.create_login_tab(), "Login")
        tabs.addTab(self.create_register_tab(), "Register")
        layout.addWidget(tabs)
        
        self.setLayout(layout)
    
    def create_login_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        layout.setSpacing(15)
        
        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Enter username")
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Enter password")
        self.login_pass.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Username:", self.login_user)
        layout.addRow("Password:", self.login_pass)
        
        btn_login = QPushButton("Login")
        btn_login.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px; font-weight: bold;")
        btn_login.clicked.connect(self.do_login)
        layout.addRow(btn_login)
        
        widget.setLayout(layout)
        return widget
    
    def create_register_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        layout.setSpacing(15)
        
        self.reg_user = QLineEdit()
        self.reg_pass = QLineEdit()
        self.reg_pass.setEchoMode(QLineEdit.Password)
        self.reg_email = QLineEdit()
        
        layout.addRow("Username:", self.reg_user)
        layout.addRow("Password:", self.reg_pass)
        layout.addRow("Email:", self.reg_email)
        
        btn_register = QPushButton("Register")
        btn_register.setStyleSheet(f"background-color: {COLOR_SECONDARY}; color: white; padding: 10px; font-weight: bold;")
        btn_register.clicked.connect(self.do_register)
        layout.addRow(btn_register)
        
        widget.setLayout(layout)
        return widget
    
    def do_login(self):
        user = self.login_user.text().strip()
        pwd = self.login_pass.text().strip()
        
        if not user or not pwd:
            QMessageBox.warning(self, "Input Error", "Please enter username and password.")
            return
        
        query = f"SELECT password_hash FROM USERS WHERE username = '{user}'"
        data, msg = self.db.fetch_results(query)
        
        if data and data[1]:
            db_hash = data[1][0][0]
            if db_hash == pwd:
                self.logged_in = True
                self.accept()
            else:
                QMessageBox.critical(self, "Login Failed", "Invalid password.")
        else:
            QMessageBox.critical(self, "Login Failed", "User not found. Please Register.")
    
    def do_register(self):
        user = self.reg_user.text().strip()
        pwd = self.reg_pass.text().strip()
        email = self.reg_email.text().strip()
        
        if not user or not pwd or not email:
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return
        
        if "@" not in email or "." not in email:
            QMessageBox.critical(self, "Validation Error", "Email must contain '@' and '.'.")
            return
        
        query = "INSERT INTO USERS (username, password_hash, email, role) VALUES (?, ?, ?, 'Customer')"
        if self.db.execute_commit(query, (user, pwd, email)):
            QMessageBox.information(self, "Success", "Registration Successful! Please Login.")
        else:
            QMessageBox.critical(self, "Error", "Registration failed.")


class BookingDialog(QDialog):
    def __init__(self, db, flight_data, parent=None):
        super().__init__(parent)
        self.db = db
        self.flight_data = flight_data
        self.flight_id = flight_data[0]
        self.base_price = float(flight_data[6])
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"Book Flight {self.flight_data[2]}")
        self.setFixedSize(450, 600)
        
        layout = QVBoxLayout()
        
        # Passenger Details
        passenger_group = QGroupBox("Passenger Details")
        form = QFormLayout()
        
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.passport = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        
        form.addRow("First Name:", self.first_name)
        form.addRow("Last Name:", self.last_name)
        form.addRow("Passport No:", self.passport)
        form.addRow("Email:", self.email)
        form.addRow("Phone:", self.phone)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems(["Economy", "Business", "First Class"])
        self.class_combo.currentIndexChanged.connect(self.update_price)
        form.addRow("Class:", self.class_combo)
        
        self.seat_combo = QComboBox()
        self.seat_combo.addItems(["1A", "1B", "1C", "2A", "2B", "2C", "3A", "3B"])
        form.addRow("Seat:", self.seat_combo)
        
        passenger_group.setLayout(form)
        layout.addWidget(passenger_group)
        
        # Payment Details
        payment_group = QGroupBox("Payment Details (SP_ProcessPayment)")
        pay_form = QFormLayout()
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Credit Card", "Debit Card", "PayPal", "Bank Transfer"])
        pay_form.addRow("Pay Method:", self.payment_combo)
        
        self.card_last4 = QLineEdit()
        self.card_last4.setMaxLength(4)
        self.card_last4.setPlaceholderText("Optional")
        pay_form.addRow("Card Last 4:", self.card_last4)
        
        payment_group.setLayout(pay_form)
        layout.addWidget(payment_group)
        
        # Price Label
        self.price_label = QLabel(f"Total Price: ${self.base_price:.2f}")
        self.price_label.setFont(QFont("Helvetica", 14, QFont.Bold))
        self.price_label.setStyleSheet("color: green; padding: 10px;")
        self.price_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.price_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_book = QPushButton("Confirm & Pay")
        btn_book.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 10px; font-weight: bold;")
        btn_book.clicked.connect(self.book_flight)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_book)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.update_price()
    
    def update_price(self):
        cls = self.class_combo.currentText()
        multipliers = {"Economy": 1.0, "Business": 2.5, "First Class": 4.0}
        self.final_price = self.base_price * multipliers.get(cls, 1.0)
        self.price_label.setText(f"Total Price: ${self.final_price:.2f}")
    
    def book_flight(self):
        fname = self.first_name.text().strip()
        lname = self.last_name.text().strip()
        passport = self.passport.text().strip()
        email = self.email.text().strip()
        phone = self.phone.text().strip()
        cls = self.class_combo.currentText()
        payment_method = self.payment_combo.currentText()
        card_last4 = self.card_last4.text().strip()
        
        # Validation
        if not all([fname, lname, passport, email, phone]):
            QMessageBox.critical(self, "Error", "All passenger fields are required.")
            return
        
        if any(char.isdigit() for char in fname) or any(char.isdigit() for char in lname):
            QMessageBox.critical(self, "Error", "Names cannot contain numbers.")
            return
        
        if "@" not in email or "." not in email:
            QMessageBox.critical(self, "Error", "Invalid email format.")
            return
        
        phone_clean = phone.replace("+", "").replace("-", "").replace(" ", "")
        if not phone_clean.isdigit() or len(phone_clean) != 11:
            QMessageBox.critical(self, "Error", "Phone must be 11 digits.")
            return
        
        try:
            # Insert Passenger
            p_query = """
            INSERT INTO PASSENGERS (first_name, last_name, date_of_birth, nationality, passport_number, passport_expiry_date, email, phone_number)
            VALUES (?, ?, '1990-01-01', 'Unknown', ?, '2030-01-01', ?, ?)
            """
            if self.db.execute_commit(p_query, (fname, lname, passport, email, phone)):
                pid_data, _ = self.db.fetch_results(f"SELECT passenger_id FROM PASSENGERS WHERE passport_number='{passport}'")
                if pid_data and pid_data[1]:
                    pid = pid_data[1][0][0]
                    ref = f"BK{random.randint(10000,99999)}"
                    
                    r_query = """
                    INSERT INTO RESERVATIONS (passenger_id, flight_id, booking_reference, seat_number, class_type, total_price, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, 'Pending')
                    """
                    if self.db.execute_commit(r_query, (pid, self.flight_id, ref, self.seat_combo.currentText(), cls, self.final_price)):
                        QMessageBox.information(self, "Success", 
                            f"Booking Successful!\n\nRef: {ref}\nPrice: ${self.final_price:.2f}\nClass: {cls}")
                        self.accept()
                    else:
                        QMessageBox.critical(self, "Error", "Failed to create reservation.")
            else:
                QMessageBox.critical(self, "Error", "Failed to register passenger.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.db.connect()
        self.runner = SQLRunner(self.db)
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Flight Reservation System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("✈ Flight Reservation System")
        header.setFont(QFont("Helvetica", 20, QFont.Bold))
        header.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_flights_tab(), "Search Flights")
        tabs.addTab(self.create_bookings_tab(), "My Bookings")
        tabs.addTab(self.create_analytics_tab(), "Analytics")
        tabs.addTab(self.create_admin_tab(), "Admin & Setup")
        layout.addWidget(tabs)
        
        central.setLayout(layout)
        
        # Load initial data
        self.refresh_flights()
        self.refresh_bookings()
    
    def create_flights_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Search Panel
        search_group = QGroupBox("Search Flights (SP_SearchFlights)")
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("From:"))
        self.combo_from = QComboBox()
        self.combo_from.setMinimumWidth(150)
        search_layout.addWidget(self.combo_from)
        
        search_layout.addWidget(QLabel("To:"))
        self.combo_to = QComboBox()
        self.combo_to.setMinimumWidth(150)
        search_layout.addWidget(self.combo_to)
        
        search_layout.addWidget(QLabel("Date:"))
        self.date_entry = QLineEdit()
        self.date_entry.setPlaceholderText("YYYY-MM-DD")
        self.date_entry.setMaximumWidth(120)
        search_layout.addWidget(self.date_entry)
        
        search_layout.addWidget(QLabel("Class:"))
        self.combo_class = QComboBox()
        self.combo_class.addItems(["Any", "Economy", "Business", "First Class"])
        search_layout.addWidget(self.combo_class)
        
        btn_search = QPushButton("🔍 Search")
        btn_search.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 8px;")
        btn_search.clicked.connect(self.search_flights)
        search_layout.addWidget(btn_search)
        
        btn_clear = QPushButton("Show All")
        btn_clear.clicked.connect(self.refresh_flights)
        search_layout.addWidget(btn_clear)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Populate airports
        self.populate_airports()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QLabel("Available Flights"))
        btn_layout.addStretch()
        btn_book = QPushButton("✓ Book Selected Flight")
        btn_book.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; padding: 8px;")
        btn_book.clicked.connect(self.book_selected_flight)
        btn_layout.addWidget(btn_book)
        layout.addLayout(btn_layout)
        
        # Flights Table
        self.flights_table = QTableWidget()
        self.flights_table.setColumnCount(9)
        self.flights_table.setHorizontalHeaderLabels(["ID", "Airline", "Flight No", "Origin", "Dest", "Departure", "Price", "Seats", "Status"])
        self.flights_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.flights_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.flights_table.doubleClicked.connect(self.book_selected_flight)
        layout.addWidget(self.flights_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_bookings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Reservation Details (VW_PassengerReservationDetails)"))
        
        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(11)
        self.bookings_table.setHorizontalHeaderLabels(["ID", "Ref", "Passenger", "Flight", "Airline", "Route", "Seat", "Class", "Status", "Payment", "Amount"])
        self.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bookings_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.bookings_table)
        
        # Action Buttons
        btn_layout = QHBoxLayout()

        btn_refresh = QPushButton("Refresh Bookings")
        btn_refresh.clicked.connect(self.refresh_bookings)
        btn_layout.addWidget(btn_refresh)

        btn_cancel = QPushButton("Cancel Reservation")
        btn_cancel.setStyleSheet(f"background-color: #dc3545; color: white; font-weight: bold;") # Red for cancel
        btn_cancel.clicked.connect(self.action_cancel)
        btn_layout.addWidget(btn_cancel)

        btn_checkin = QPushButton("Check-In")
        btn_checkin.setStyleSheet(f"background-color: {COLOR_PRIMARY}; color: white; font-weight: bold;")
        btn_checkin.clicked.connect(self.action_checkin)
        btn_layout.addWidget(btn_checkin)

        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_analytics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Airline Performance
        layout.addWidget(QLabel("Airline Performance (VW_AirlinePerformance)"))
        self.analytics_table1 = QTableWidget()
        self.analytics_table1.setColumnCount(5)
        self.analytics_table1.setHorizontalHeaderLabels(["Airline", "Flights", "Passengers", "Occupancy %", "Revenue"])
        self.analytics_table1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.analytics_table1)
        
        # Flight Statistics
        layout.addWidget(QLabel("Flight Statistics (VW_FlightStatistics)"))
        self.analytics_table2 = QTableWidget()
        self.analytics_table2.setColumnCount(8)
        self.analytics_table2.setHorizontalHeaderLabels(["Flight", "Airline", "Departure", "Total", "Available", "Booked", "Occupancy %", "Revenue"])
        self.analytics_table2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.analytics_table2)
        
        btn_refresh = QPushButton("Refresh Analytics")
        btn_refresh.clicked.connect(self.refresh_analytics)
        layout.addWidget(btn_refresh)
        
        widget.setLayout(layout)
        return widget
    
    def create_admin_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        
        btn_connect = QPushButton("Re-Connect Database")
        btn_connect.clicked.connect(self.connect_db)
        btn_layout.addWidget(btn_connect)
        
        btn_run_scripts = QPushButton("Run All SQL Scripts")
        btn_run_scripts.clicked.connect(self.run_all_scripts)
        btn_layout.addWidget(btn_run_scripts)
        
        btn_tables = QPushButton("Show Tables")
        btn_tables.clicked.connect(self.show_tables)
        btn_layout.addWidget(btn_tables)
        
        layout.addLayout(btn_layout)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_area)
        
        widget.setLayout(layout)
        return widget
    
    def populate_airports(self):
        query = "SELECT airport_id, city + ' (' + airport_code + ')' AS display FROM AIRPORTS WHERE status = 'Operational' ORDER BY city"
        data, msg = self.db.fetch_results(query)
        if data and data[1]:
            self.airport_list = [(row[0], row[1]) for row in data[1]]
            for aid, display in self.airport_list:
                self.combo_from.addItem(display, aid)
                self.combo_to.addItem(display, aid)
    
    def refresh_flights(self):
        self.flights_table.setRowCount(0)
        query = """SELECT flight_id, airline_name, flight_number, departure_city, arrival_city, 
                   departure_datetime, base_price, available_seats, status 
                   FROM VW_AvailableFlights ORDER BY departure_datetime"""
        data, msg = self.db.fetch_results(query)
        if data and data[1]:
            for row in data[1]:
                row_pos = self.flights_table.rowCount()
                self.flights_table.insertRow(row_pos)
                for col, val in enumerate(row):
                    self.flights_table.setItem(row_pos, col, QTableWidgetItem(str(val)))
    
    def search_flights(self):
        from_idx = self.combo_from.currentIndex()
        to_idx = self.combo_to.currentIndex()
        travel_date = self.date_entry.text().strip()
        
        if from_idx < 0 or to_idx < 0 or not travel_date:
            QMessageBox.warning(self, "Input Required", "Please select airports and date.")
            return
        
        if from_idx == to_idx:
            QMessageBox.critical(self, "Error", "Origin and Destination cannot be the same.")
            return
        
        try:
            travel_date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()
            if travel_date_obj < date.today():
                QMessageBox.critical(self, "Error", f"Date has passed. Please enter a future date.")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid date format. Use YYYY-MM-DD.")
            return
        
        dep_id = self.combo_from.currentData()
        arr_id = self.combo_to.currentData()
        
        self.flights_table.setRowCount(0)
        query = "EXEC SP_SearchFlights @departure_airport_id=?, @arrival_airport_id=?, @travel_date=?"
        data, msg = self.db.fetch_results(query, (dep_id, arr_id, travel_date))
        if data and data[1]:
            for row in data[1]:
                row_pos = self.flights_table.rowCount()
                self.flights_table.insertRow(row_pos)
                display_row = [row[0], row[2], row[1], row[5], row[7], row[8], row[11], row[12], row[14]]
                for col, val in enumerate(display_row):
                    self.flights_table.setItem(row_pos, col, QTableWidgetItem(str(val)))
        else:
            QMessageBox.information(self, "No Results", "No flights found.")
    
    def book_selected_flight(self):
        selected = self.flights_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection", "Please select a flight.")
            return
        
        row = self.flights_table.currentRow()
        flight_data = [self.flights_table.item(row, col).text() for col in range(9)]
        
        dialog = BookingDialog(self.db, flight_data, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_flights()
            self.refresh_bookings()
    
    def refresh_bookings(self):
        self.bookings_table.setRowCount(0)
        query = """SELECT TOP 20 reservation_id, booking_reference, passenger_name, flight_number, 
                   airline_name, departure_city + ' → ' + arrival_city, seat_number, class_type,
                   reservation_status, payment_status, total_price
                   FROM VW_PassengerReservationDetails ORDER BY booking_date DESC"""
        data, msg = self.db.fetch_results(query)
        if data and data[1]:
            for row in data[1]:
                row_pos = self.bookings_table.rowCount()
                self.bookings_table.insertRow(row_pos)
                for col, val in enumerate(row):
                    self.bookings_table.setItem(row_pos, col, QTableWidgetItem(str(val)))
    
    def refresh_analytics(self):
        # Airline Performance
        self.analytics_table1.setRowCount(0)
        q1 = "SELECT airline_name, total_flights, total_passengers, avg_occupancy_rate, total_revenue FROM VW_AirlinePerformance"
        d1, _ = self.db.fetch_results(q1)
        if d1 and d1[1]:
            for row in d1[1]:
                row_pos = self.analytics_table1.rowCount()
                self.analytics_table1.insertRow(row_pos)
                for col, val in enumerate(row):
                    self.analytics_table1.setItem(row_pos, col, QTableWidgetItem(str(val)))
        
        # Flight Statistics
        self.analytics_table2.setRowCount(0)
        q2 = """SELECT flight_number, airline_name, departure_datetime, total_seats, available_seats,
                booked_seats, occupancy_percentage, total_revenue FROM VW_FlightStatistics"""
        d2, _ = self.db.fetch_results(q2)
        if d2 and d2[1]:
            for row in d2[1]:
                row_pos = self.analytics_table2.rowCount()
                self.analytics_table2.insertRow(row_pos)
                for col, val in enumerate(row):
                    self.analytics_table2.setItem(row_pos, col, QTableWidgetItem(str(val)))
    
    def connect_db(self):
        success, msg = self.db.connect()
        self.log_area.append(msg)
        if success:
            self.refresh_flights()
    
    def run_all_scripts(self):
        reply = QMessageBox.question(self, "Confirm", "This will reset the database. Continue?")
        if reply == QMessageBox.Yes:
            self.log_area.append("Running scripts...")
            success, msg = self.runner.run_all_scripts(self.project_dir)
            self.log_area.append(msg)
            self.db.connect()
            self.refresh_flights()
    
    def show_tables(self):
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
        data, msg = self.db.fetch_results(query)
        if data and data[1]:
            self.log_area.append("Tables found:")
            for r in data[1]:
                self.log_area.append(f"  - {r[0]}")

    def action_cancel(self):
        selected = self.bookings_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection", "Please select a reservation to cancel.")
            return

        row = self.bookings_table.currentRow()
        # Columns: ["ID", "Ref", "Passenger", "Flight", "Airline", "Route", "Seat", "Class", "Status", "Payment", "Amount"]
        # ID is at index 0, Status is at index 8
        res_id = self.bookings_table.item(row, 0).text()
        status = self.bookings_table.item(row, 8).text()

        if status == 'Cancelled':
            QMessageBox.information(self, "Info", "Already cancelled.")
            return

        reply = QMessageBox.question(self, "Confirm Cancel", "Are you sure you want to cancel? Refund rules apply.",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # Call SP_CancelReservation
                sql = """\
                DECLARE @refund DECIMAL(10,2);
                EXEC SP_CancelReservation ?, 'User Requested', @refund OUTPUT;
                SELECT @refund;
                """
                data, msg = self.db.fetch_results(sql, (res_id,))
                
                if data and data[1]:
                    refund = data[1][0][0]
                    QMessageBox.information(self, "Cancelled", f"Reservation Cancelled.\nRefund Amount: ${refund}")
                    self.refresh_bookings()
                    self.refresh_analytics()
                else:
                     QMessageBox.critical(self, "Error", f"Cancellation failed: {msg}")

            except Exception as e:
                 QMessageBox.critical(self, "Error", str(e))

    def action_checkin(self):
        selected = self.bookings_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection", "Please select a reservation to check-in.")
            return

        row = self.bookings_table.currentRow()
        res_id = self.bookings_table.item(row, 0).text()
        status = self.bookings_table.item(row, 8).text()

        if status == 'Cancelled':
            QMessageBox.critical(self, "Error", "Cannot check-in a cancelled reservation.")
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
                QMessageBox.information(self, "Boarding Pass", pass_info)
                self.refresh_bookings()
            else:
                 QMessageBox.critical(self, "Error", f"Check-in failed: {msg}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


def main():
    app = QApplication(sys.argv)
    
    # Show login dialog first
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted and login.logged_in:
        # Show main window
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
