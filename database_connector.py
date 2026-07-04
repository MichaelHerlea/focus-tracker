import sqlite3
import time

from application_tracker import ApplicationData

database_filename = "database.db"

class Database():
    def __init__(self):
        self.connection_obj = sqlite3.connect(database_filename)
        self.connection_obj.execute("PRAGMA foreign_keys = ON;")
        self.cursor_obj = self.connection_obj.cursor()
        
        create_application_category_table_query = "CREATE TABLE IF NOT EXISTS application_categories (" \
        "id INTEGER PRIMARY KEY AUTOINCREMENT," \
        "name VARCHAR(255) NOT NULL UNIQUE);"
        self.cursor_obj.execute(create_application_category_table_query)
        insert_into_application_category = "INSERT OR IGNORE INTO application_categories (name) VALUES (?)"
        self.cursor_obj.execute(insert_into_application_category, ("productivity",))
        self.cursor_obj.execute(insert_into_application_category, ("entertainment",))
        self.cursor_obj.execute(insert_into_application_category, ("other",))

        create_application_table_query ="CREATE TABLE IF NOT EXISTS applications (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "name VARCHAR(255) NOT NULL UNIQUE," \
            "category_id INTEGER NOT NULL," \
            "FOREIGN KEY (category_id) REFERENCES application_categories(id));"
        self.cursor_obj.execute(create_application_table_query)

        create_report_table_query = "CREATE TABLE IF NOT EXISTS reports (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "created_at FLOAT NOT NULL," \
            "ended_at FLOAT NOT NULL);"
        self.cursor_obj.execute(create_report_table_query)

        create_events_table_query = "CREATE TABLE IF NOT EXISTS events (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "report_id INTEGER NOT NULL," \
            "application_id INTEGER NOT NULL," \
            "switched_at FLOAT NOT NULL," \
            "FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE," \
            "FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE);"
        self.cursor_obj.execute(create_events_table_query)
        self.connection_obj.commit()

    def create_report(self, data: ApplicationData):
        if not data._tab_switches:
            return
        report_id = self.start_new_report(data._tab_switches[0][1])
        for element in data._tab_switches:
            self.record_tab_switch(report_id, element[0], element[1])
        return report_id
    
    def start_new_report(self, created_at):
        create_new_report_query = "INSERT INTO reports (created_at, ended_at) VALUES (?, ?)"
        self.cursor_obj.execute(create_new_report_query, (created_at, time.time()))
        self.connection_obj.commit()
        return self.cursor_obj.lastrowid
    
    def get_category_id(self, text):
        get_category_id_query = "SELECT id FROM application_categories WHERE name = ?"
        self.cursor_obj.execute(get_category_id_query, (text,))
        return self.cursor_obj.fetchone()[0]

    def get_or_create_application_id(self, name):
        get_application_id = "SELECT id FROM applications WHERE name = ?"
        create_application = "INSERT INTO applications (name, category_id) VALUES (?, ?)"

        self.cursor_obj.execute(get_application_id, (name,))
        application_id = self.cursor_obj.fetchone()
        if not application_id:
            self.cursor_obj.execute(create_application, (name, self.get_category_id("other")))
            self.connection_obj.commit()
            return self.cursor_obj.lastrowid
        else:
            self.connection_obj.commit()
            return application_id[0]
    
    def record_tab_switch(self, report_id, name, time):
        record_tab_switch_query = "INSERT INTO events (report_id, application_id, switched_at) VALUES (?, ?, ?)"
        self.connection_obj.execute(record_tab_switch_query, (report_id, self.get_or_create_application_id(name), time))
        self.connection_obj.commit()

    def delete_report(self, entry_id):
        delete_report_query = "DELETE FROM reports WHERE id = ?"
        self.cursor_obj.execute(delete_report_query, (entry_id,))
        self.connection_obj.commit()
    
    def update_application_category(self, name, category_text):
        get_category_id = "SELECT id FROM application_categories WHERE name = ?"
        self.cursor_obj.execute(get_category_id, (category_text, ))
        category_id = self.cursor_obj.fetchone()[0]
        update_application_category = "UPDATE applications SET category_id = ? WHERE name = ?"
        self.cursor_obj.execute(update_application_category, (category_id, name))
        self.connection_obj.commit()
    
    def get_pie_chart_data(self, report_id):
        get_pie_chart_data_query = """WITH EventDurations AS (
            SELECT 
                e.application_id,
                COALESCE(
                    LEAD(e.switched_at) OVER (PARTITION BY e.report_id ORDER BY e.switched_at), 
                    r.ended_at
                ) - e.switched_at AS duration
            FROM events e
            JOIN reports r ON e.report_id = r.id
            WHERE e.report_id = ?
        )
        SELECT 
            a.name,
            SUM(ed.duration)
        FROM EventDurations ed
        JOIN applications a ON ed.application_id = a.id
        GROUP BY a.id, a.name
        ORDER BY SUM(ed.duration) DESC;"""
        
        self.cursor_obj.execute(get_pie_chart_data_query, (report_id,))
        return self.cursor_obj.fetchall()

    def get_productivity_score(self, report_id):
        get_productivity_score_query = """WITH EventDurations AS (
            SELECT 
                e.application_id,
                COALESCE(
                    LEAD(e.switched_at) OVER (PARTITION BY e.report_id ORDER BY e.switched_at), 
                    r.ended_at
                ) - e.switched_at AS duration
            FROM events e
            JOIN reports r ON e.report_id = r.id
            WHERE e.report_id = ?
        ),
        CategoryTotals AS (
            SELECT 
                c.name,
                SUM(ed.duration) AS total_duration
            FROM EventDurations ed
            JOIN applications a ON ed.application_id = a.id
            JOIN application_categories c ON a.category_id = c.id
            WHERE c.name IN ('productivity', 'entertainment')
            GROUP BY c.name
        )
        SELECT 
            SUM(CASE WHEN name = 'productivity' THEN total_duration ELSE 0 END) * 1.0 /
            NULLIF(SUM(total_duration), 0) AS productivity_score
        FROM CategoryTotals;"""

        self.cursor_obj.execute(get_productivity_score_query, (report_id,))
        score = self.cursor_obj.fetchone()[0]
        if score is None:
            return score
        return round(score * 100)
    
    def get_application_category_list(self, report_id):
        get_application_category_list_query = "SELECT DISTINCT a.name, c.name FROM events e JOIN applications a ON e.application_id = a.id JOIN application_categories c ON a.category_id = c.id WHERE e.report_id = ?;"
        self.cursor_obj.execute(get_application_category_list_query, (report_id,))
        return self.cursor_obj.fetchall()
    
    def get_list_of_reports(self):
        get_list_of_reports_query = "SELECT id FROM reports"
        self.cursor_obj.execute(get_list_of_reports_query)
        return self.cursor_obj.fetchall()