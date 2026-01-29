import os
import re

class SQLRunner:
    def __init__(self, db_connection):
        self.db = db_connection

    def run_script(self, file_path):
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"Error reading file: {e}"

        # Split by GO command (case insensitive), handling varying whitespace
        # Regex looks for GO on its own line or surrounded by whitespace
        commands = re.split(r'\bGO\b', content, flags=re.IGNORECASE)

        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
            
            success, msg = self.db.execute_query(cmd)
            if not success:
                return False, f"Error in {os.path.basename(file_path)}: {msg}"
        
        return True, f"Successfully executed {os.path.basename(file_path)}"

    def run_all_scripts(self, directory):
        # Find all SQLQuery_*.sql files and sort them
        files = [f for f in os.listdir(directory) if f.startswith('SQLQuery_') and f.endswith('.sql')]
        files.sort() # SQLQuery_0.sql, SQLQuery_1.sql, etc.

        if not files:
            return False, "No SQLQuery_*.sql files found."

        results = []
        for file_name in files:
            full_path = os.path.join(directory, file_name)
            success, msg = self.run_script(full_path)
            results.append(msg)
            if not success:
                return False, "\n".join(results)
        
        return True, "All scripts executed successfully.\n" + "\n".join(results)
