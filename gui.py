from PyQt6.QtWidgets import * # type: ignore
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from application_tracker import ApplicationTracker, ApplicationSpecificData

class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.application_tracker = ApplicationTracker()

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

        self.setLayout(main_layout)
    
    def on_start_button_clicked(self):
        self.status_indicator.set_color("green")
        self.pie_chart.update_chart({})
        self.application_tracker.start()
    
    def on_stop_button_clicked(self):
        self.application_tracker.stop()
        self.status_indicator.set_color("red")
        self.pie_chart.update_chart(ApplicationSpecificData.get_chart_data())
        #print(ApplicationSpecificData.get_all_instances_to_string())

class StatusIndicator(QLabel):
    def __init__(self) -> None:
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