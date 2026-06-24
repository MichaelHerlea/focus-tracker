import sqlite3

class DatabaseInitializer():
    def __init__(self):
        self.connection_obj = sqlite3.connect("database.db")
        self.cursor_obj = self.connection_obj.cursor()

        create_application_table_query ="CREATE TABLE IF NOT EXISTS applications (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "name VARCHAR(255) NOT NULL);"
        self.cursor_obj.execute(create_application_table_query)

        create_report_table_query = "CREATE TABLE IF NOT EXISTS reports (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);"
        self.cursor_obj.execute(create_report_table_query)

        create_report_entries_table_query = "CREATE TABLE IF NOT EXISTS report_entries (" \
            "report_id INTEGER NOT NULL," \
            "application_id INTEGER NOT NULL," \
            "time_spent INTEGER NOT NULL," \
            "PRIMARY KEY (report_id, application_id)," \
            "FOREIGN KEY (report_id) REFERENCES reports(id)," \
            "FOREIGN KEY (application_id) REFERENCES applications(id));"
        self.cursor_obj.execute(create_report_entries_table_query)

class ReportDatabaseHandler():
    def __init__(self):
        self.connection_obj = sqlite3.connect("database.db")
        self.cursor_obj = self.connection_obj.cursor()
    
    def add_report(self, data):
        if not data:
            return
        add_report_query = "INSERT INTO reports DEFAULT VALUES"
        self.cursor_obj.execute(add_report_query)
        report_id = self.cursor_obj.lastrowid

        add_report_entries_query = "INSERT INTO report_entries VALUES (?, ?, ?)"
        get_application_id = "SELECT id FROM applications WHERE name = ?"
        add_application = "INSERT INTO applications (name) VALUES (?)"
        for name in data.keys():
            self.cursor_obj.execute(get_application_id, (name,))
            row = self.cursor_obj.fetchone()
            if row == None:
                self.cursor_obj.execute(add_application, (name,))
                application_id = self.cursor_obj.lastrowid
            else:
                application_id = row[0]
            
            self.cursor_obj.execute(add_report_entries_query, (report_id, application_id, data[name]))
        self.connection_obj.commit()