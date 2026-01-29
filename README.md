# Flight Reservation System

A comprehensive desktop application for managing flight reservations, built with Python and SQL Server. This project offers two GUI implementations: one using **Tkinter** and another using **PyQt5**.

## Features

- **User Management**: Secure Login and Registration for customers.
- **Flight Search**: Search for flights by origin, destination, date, and class/category.
- **Booking System**: Book flights with passenger details (Passport, Name, etc.) and simulate payments.
- **My Bookings**: View booking history, check-in to generate a boarding pass, or cancel reservations.
- **Analytics Dashboard**: Visual insights into airline performance, daily revenue, and flight statistics.
- **Admin Tools**:
    - **Database Setup**: One-click initialization of the database schema and dummy data.
    - **Flight Status**: Update flight statuses (e.g., Delayed, Arrived) which triggers audit logs.
    - **Logs**: View system audit logs.

## Prerequisites

- **Python 3.x**
- **Microsoft SQL Server** (Local or Remote instance)
- **ODBC Driver for SQL Server** (Driver 18, 17, or 13 recommended)

## Installation

1.  **Clone the repository** (if applicable) or download the source code.

2.  **Install Dependencies**:
    This project requires `pyodbc` for database connectivity and `PyQt5` for the modern GUI.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you only plan to use the Tkinter version, `PyQt5` is optional.*

3.  **Database Configuration**:
    The application connects to a local SQL Server instance by default. Open `database_connection.py` and verify/update the connection string settings if your setup differs:
    ```python
    self.connection_string_template = (
        "DRIVER={{{driver}}};"
        "SERVER=localhost,1433;"  # Update Server Address if needed
        "DATABASE=FlightReservationDB;"
        "UID=sa;"                 # Update Username
        "PWD=DB_Password123!;"    # Update Password
        "TrustServerCertificate=yes;"
    )
    ```
    *Ensure your SQL Server instance allows SQL Server Authentication and the user has permissions to create databases.*

## Usage

### 1. Database Initialization
You can initialize the database directly from the application's Admin tab.
- Run either GUI application (see below).
- Go to the **Admin & Setup** tab.
- Click **Run All SQL Scripts (Reset DB)**. This will execute the SQL scripts in the directory to set up the tables, views, stored procedures, and sample data.

### 2. Running the Application

**Option A: Tkinter GUI (Standard Library)**
A lightweight interface using Python's built-in GUI library.
```bash
python gui.py
```

**Option B: PyQt5 GUI (Modern Interface)**
A robust and modern interface using PyQt5.
```bash
python gui_pyqt.py
```

## Project Structure

- `start.py` / `gui.py`: Main entry point for Tkinter GUI.
- `gui_pyqt.py`: Main entry point for PyQt5 GUI.
- `database_connection.py`: Handles database connectivity and connection strings.
- `sql_runner.py`: Helper script to execute SQL files for setup.
- `SQLQuery_*.sql` & `generate_dummy_data.sql`: SQL scripts for schema, logic, and data generation.
- `requirements.txt`: Python package dependencies.
