from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from application_tracker import ApplicationTracker, ApplicationData
from database_connector import DatabaseInitializer, ReportDatabaseHandler

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        temp_var = ["Report id: 1, Timestamp: 21min",
            "Report id: 2, Timestamp: 24min",
            "Report id: 3, Timestamp: 35min"]

        self.application_tracker = ApplicationTracker()
        self.database_Initializer = DatabaseInitializer()
        self.report_database_handler = ReportDatabaseHandler(self.database_Initializer)

        self.setWindowTitle("Focus tracker")

        main_layout = QVBoxLayout()

        control_panel = QHBoxLayout()
        start_button = QPushButton("Start")
        start_button.clicked.connect(self.on_start_button_clicked)
        control_panel.addWidget(start_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.on_stop_button_clicked)
        control_panel.addWidget(stop_button)

        self.status_indicator = StatusIndicator()
        control_panel.addWidget(self.status_indicator)
        main_layout.addLayout(control_panel)

        self.pie_chart = PieChartWidget()
        main_layout.addWidget(self.pie_chart)

        self.report_list = ReportList(self.report_database_handler, self.pie_chart)
        main_layout.addWidget(self.report_list)

        self.setLayout(main_layout)
    
    def on_start_button_clicked(self):
        self.status_indicator.set_color("green")
        self.pie_chart.update_chart({})
        self.application_tracker.start()
    
    def on_stop_button_clicked(self):
        self.application_tracker.stop()
        self.status_indicator.set_color("red")
        self.pie_chart.update_chart(ApplicationData.get_data())
        self.report_database_handler.add_report(ApplicationData.get_data())
        self.report_list.update_list()
        ApplicationData.clear_data()

class ReportList(QWidget):
    def __init__(self, report_database_handler: ReportDatabaseHandler, pie_chart: PieChartWidget):
        super().__init__()

        self.report_database_handler = report_database_handler
        self.list = None
        self.pie_chart = pie_chart

        self.main_layout = QVBoxLayout()
        self.update_list()
        self.setLayout(self.main_layout)

    def update_list(self):
        self.clear_list()
        self.list = self.report_database_handler.get_report_list()
        for entry in self.list:
            self.main_layout.addWidget(ReportItem(entry, self))
    
    def clear_list(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget() # type: ignore
            if widget is not None:
                widget.deleteLater()

    def delete_entry(self, entry_id):
        self.report_database_handler.delete_report(entry_id)
        self.update_list()
    
    def load_report(self, entry_id):
        self.pie_chart.update_chart(dict(self.report_database_handler.get_report_contents(entry_id)))

class ReportItem(QWidget):
    def __init__(self, list, parent_list: ReportList):
        super().__init__()

        self.parent_list = parent_list

        main_layout = QHBoxLayout()

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        text = QLabel(f"ID: {list[0]}, timestamp: {list[1]}")
        main_layout.addWidget(text)

        open_button = QPushButton("Open")
        open_button.clicked.connect(lambda: self.open_button_handler(list[0]))
        main_layout.addWidget(open_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_button_handler(list[0]))
        main_layout.addWidget(delete_button)

        self.setLayout(main_layout)
    
    def open_button_handler(self, entry_id):
        self.parent_list.load_report(entry_id)
    
    def delete_button_handler(self, entry_id):
        self.parent_list.delete_entry(entry_id)

class StatusIndicator(QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 16)
        self.set_color("red")        

    def set_color(self, color):
        self.setStyleSheet(f"""
            background-color: {color};
            border-radius: 8px;
        """)

class PieChartWidget(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.update_chart({})

    def update_chart(self, data: dict):
        self.ax.clear()

        if not data:
            self.ax.set_title("Time per Application")
            self.ax.set_axis_off()
            self.draw()
            return

        labels = list(f"{name} ({int(value)}s)"for name, value in data.items())
        values = list(data.values())

        self.ax.pie(values, labels=labels, autopct="%1.1f%%")
        self.ax.set_title("Time per Application")

        self.draw()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()