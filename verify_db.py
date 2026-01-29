from database_connection import DatabaseConnection
from sql_runner import SQLRunner
import os

def main():
    print("Initializing database connection...")
    db = DatabaseConnection()
    success, msg = db.connect()
    print(msg)
    if not success:
        print("Failed to connect to database.")
        return

    print("Initializing SQL Runner...")
    runner = SQLRunner(db)
    
    current_dir = os.getcwd()
    print(f"Running scripts in: {current_dir}")
    
    success, msg = runner.run_all_scripts(current_dir)
    print(msg)
    
    db.disconnect()

if __name__ == "__main__":
    main()
