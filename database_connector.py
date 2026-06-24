import sqlite3

class DatabaseInitializer():
    def __init__(self):
        self.connection_obj = sqlite3.connect("database.db")
        self.connection_obj.execute("PRAGMA foreign_keys = ON;")
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
            "FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE," \
            "FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE);"
        self.cursor_obj.execute(create_report_entries_table_query)
        self.connection_obj.commit()

class ReportDatabaseHandler():
    def __init__(self, database_connection: DatabaseInitializer):
        self.connection_obj = database_connection.connection_obj
        self.cursor_obj = database_connection.cursor_obj
    
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

    def get_report_list(self):
        get_report_list_query = "SELECT id, created_at FROM reports"
        self.cursor_obj.execute(get_report_list_query)
        return self.cursor_obj.fetchall()

    def delete_report(self, entry_id):
        delete_report_query = "DELETE FROM reports WHERE id = ?"
        self.cursor_obj.execute(delete_report_query, (entry_id,))
        self.connection_obj.commit()
    
    def get_report_contents(self, entry_id):
        get_report_contents_query = "SELECT a.name, re.time_spent FROM report_entries re JOIN applications a ON re.application_id = a.id WHERE re.report_id = ?"
        self.cursor_obj.execute(get_report_contents_query, (entry_id,))
        return self.cursor_obj.fetchall()