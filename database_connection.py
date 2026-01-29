import pyodbc

class DatabaseConnection:
    def __init__(self):
        self.drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server"
        ]
        self.connection_string_template = (
            "DRIVER={{{driver}}};"
            "SERVER=localhost,1433;"
            "DATABASE=FlightReservationDB;"
            "UID=sa;"
            "PWD=DB_Password123!;"
            "TrustServerCertificate=yes;"
        )
        self.conn = None

    def connect(self):
        last_error = None
        for driver in self.drivers:
            try:
                conn_str = self.connection_string_template.format(driver=driver)
                # Try connecting to the specific database
                self.conn = pyodbc.connect(conn_str, autocommit=True)
                return True, f"Connected successfully using {driver}."
            except pyodbc.Error as e:
                last_error = e
                # Fallback to master if FlightReservationDB doesn't exist yet (first run)
                # ... existing fallback logic adapted ...
                if "4060" in str(e) or "Cannot open database" in str(e):
                     try:
                        fallback_conn_str = conn_str.replace("DATABASE=FlightReservationDB;", "DATABASE=master;")
                        self.conn = pyodbc.connect(fallback_conn_str, autocommit=True)
                        return True, f"Connected to 'master' using {driver} (FlightReservationDB not found)."
                     except pyodbc.Error as e2:
                        last_error = e2
                        continue # Try next driver
        
        return False, f"All drivers failed. Last error: {last_error}"

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            return True, "Disconnected."
        return False, "No active connection."

    def execute_query(self, query):
        if not self.conn:
            return False, "Not connected to database."
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return True, "Query executed."
        except pyodbc.Error as e:
            return False, f"Execution failed: {e}"

    def execute_commit(self, query, params=None):
        """Executes INSERT/UPDATE/DELETE queries with parameters safely."""
        if not self.conn:
            return False, "Not connected to database."
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return True, "Operation successful."
        except pyodbc.Error as e:
            return False, f"Operation failed: {e}"

    def fetch_results(self, query, params=None):
        if not self.conn:
            return None, "Not connected to database."
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            # Iterate through result sets to find the first one with data (skipping row counts/prints)
            while True:
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results = cursor.fetchall()
                    return (columns, results), "Success"
                
                # Move to next result set, break if no more
                if not cursor.nextset():
                    break
            
            return ([], []), "No results returned"
            
        except pyodbc.Error as e:
            return None, f"Fetch failed: {e}"
