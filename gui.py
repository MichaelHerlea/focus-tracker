from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from application_tracker import ApplicationTracker
from database_connector import Database

plt.rcParams.update({
    "text.color": "white",
    "axes.labelcolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "axes.edgecolor": "white",
})

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.database = Database()
        self.application_tracker = ApplicationTracker()
        self.application_data = self.application_tracker.application_data

        self.currently_loaded_report_id = None

        self.setWindowTitle("Focus tracker")

        content_layout = QVBoxLayout()

        control_panel = QHBoxLayout()
        start_button = QPushButton("Start")
        start_button.clicked.connect(self.on_start_button_clicked)
        control_panel.addWidget(start_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.on_stop_button_clicked)
        control_panel.addWidget(stop_button)

        self.status_indicator = StatusIndicator()
        control_panel.addWidget(self.status_indicator)
        content_layout.addLayout(control_panel)

        self.pie_chart = PieChartWidget()
        self.pie_chart.setFixedHeight(350)
        content_layout.addWidget(self.pie_chart)

        self.timeline_chart = TimelineChartWidget()
        self.timeline_chart.setFixedHeight(220)
        content_layout.addWidget(self.timeline_chart)

        report_interaction_layout = QHBoxLayout()
        self.report_list = ReportList(self)
        report_list_scroll = NestedScrollArea()
        report_list_scroll.setWidget(self.report_list)
        report_list_scroll.setWidgetResizable(True)
        report_list_scroll.setFixedHeight(200)
        report_interaction_layout.addWidget(report_list_scroll)

        self.application_category = ApplicationCategoryList(self)
        application_category_scroll = NestedScrollArea()
        application_category_scroll.setWidget(self.application_category)
        application_category_scroll.setWidgetResizable(True)
        application_category_scroll.setFixedHeight(200)
        report_interaction_layout.addWidget(application_category_scroll)
        content_layout.addLayout(report_interaction_layout)

        self.line_chart = LineChartWidget()
        self.line_chart.setFixedHeight(220)
        content_layout.addWidget(self.line_chart)

        content_layout.addStretch()

        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

        self.load_report(None)

        self.resize(800, 800)
    
    def on_start_button_clicked(self):
        self.status_indicator.set_color("green")
        self.load_report(None)
        self.application_tracker.start()
    
    def on_stop_button_clicked(self):
        self.application_tracker.stop()
        self.status_indicator.set_color("red")
        report_id = self.database.create_report(self.application_data)
        self.application_data.clear_data()
        self.load_report(report_id)
    
    def update_application_category(self, name, text):
        self.database.update_application_category(name, text)
        self.load_report(self.currently_loaded_report_id)
    
    def delete_report(self, report_id):
        self.database.delete_report(report_id)
        self.load_report(None)

    def load_report(self, report_id):
        self.pie_chart.update_chart(dict(self.database.get_pie_chart_data(report_id)))
        self.timeline_chart.update_chart(self.database.get_timeline_data(report_id))
        self.application_category.update_list(self.database.get_application_category_list(report_id))
        self.report_list.update_list(self.database.get_list_of_reports())
        self.line_chart.update_chart(self.database.get_score_history())
        self.currently_loaded_report_id = report_id
    
    def get_productivity_score(self, report_id):
        return self.database.get_productivity_score(report_id)

class ApplicationCategoryList(QWidget):
    def __init__(self, parent_obj):
        super().__init__()

        self.list = None
        self.parent_obj = parent_obj
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.main_layout)

    def update_list(self, list):
        self.clear_list()
        self.list = list
        for entry in self.list:
            self.main_layout.addWidget(ApplicationCategoryItem(entry, self))
    
    def clear_list(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget() # type: ignore
            if widget is not None:
                widget.deleteLater()
    
    def update_database(self, name, text):
        self.parent_obj.update_application_category(name, text)

class ApplicationCategoryItem(QWidget):
    def __init__(self, list, parent: ApplicationCategoryList):
        super().__init__()

        self.parent_list = parent

        main_layout = QHBoxLayout()

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        text = QLabel(f"{list[0]}")
        main_layout.addWidget(text)

        self.dropdown = QComboBox()
        self.dropdown.addItems(["productivity", "entertainment", "other"])
        self.dropdown.setCurrentText(list[1])
        self.dropdown.currentTextChanged.connect(lambda text: self.dropdown_change(list[0], text))
        main_layout.addWidget(self.dropdown)

        self.setLayout(main_layout)

    def dropdown_change(self, name, text):
        self.parent_list.update_database(name, text)

class ReportList(QWidget):
    def __init__(self, parent_obj):
        super().__init__()

        self.parent_obj = parent_obj
        self.list = None

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.main_layout)

    def update_list(self, list):
        self.clear_list()
        self.list = list
        for entry in self.list:
            self.main_layout.insertWidget(0, ReportItem(entry[0], self))
    
    def clear_list(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget() # type: ignore
            if widget is not None:
                widget.deleteLater()

    def delete_entry(self, report_id):
        self.parent_obj.delete_report(report_id)
    
    def load_report(self, report_id):
        self.parent_obj.load_report(report_id)
    
    def get_productivity_score(self, report_id):
        return self.parent_obj.get_productivity_score(report_id)

class ReportItem(QWidget):
    def __init__(self, id, parent_list: ReportList):
        super().__init__()

        self.parent_list = parent_list

        main_layout = QHBoxLayout()

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        text = QLabel(f"ID: {id}, Score: {self.parent_list.get_productivity_score(id)}")
        main_layout.addWidget(text)

        open_button = QPushButton("Display")
        open_button.clicked.connect(lambda: self.open_button_handler(id))
        main_layout.addWidget(open_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_button_handler(id))
        main_layout.addWidget(delete_button)

        self.setLayout(main_layout)
    
    def open_button_handler(self, entry_id):
        self.parent_list.load_report(entry_id)
    
    def delete_button_handler(self, entry_id):
        self.parent_list.delete_entry(entry_id)

class NestedScrollArea(QScrollArea):
    def wheelEvent(self, event):
        bar = self.verticalScrollBar()
        delta = event.angleDelta().y()
        at_top = bar.value() <= bar.minimum() # type: ignore
        at_bottom = bar.value() >= bar.maximum() # type: ignore
        if (delta > 0 and at_top) or (delta < 0 and at_bottom):
            event.ignore()
        else:
            super().wheelEvent(event)

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

        self.fig = Figure(facecolor="none")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("none")
        super().__init__(self.fig)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
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

    def wheelEvent(self, event):
        event.ignore()

class LineChartWidget(FigureCanvasQTAgg):
    def __init__(self):

        self.fig = Figure(facecolor="none")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("none")
        super().__init__(self.fig)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.update_chart([])

    def update_chart(self, data: list):
        self.ax.clear()

        if not data:
            self.ax.set_title("Focus Score History")
            self.ax.set_axis_off()
            self.draw()
            return

        report_ids, scores = zip(*data)

        self.ax.plot(report_ids, scores, marker="o")
        self.ax.set_title("Focus Score History")
        self.ax.set_ylabel("Productivity Score (%)")
        self.ax.set_ylim(0, 100)
        self.ax.set_xticks(report_ids)

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.draw()

    def wheelEvent(self, event):
        event.ignore()

class TimelineChartWidget(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure(facecolor="none")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("none")
        super().__init__(self.fig)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.color_map = {}
        self.update_chart([])

    def get_color(self, app_name):
        if app_name not in self.color_map:
            cmap = plt.get_cmap("tab20")
            self.color_map[app_name] = cmap(len(self.color_map) % 20)
        return self.color_map[app_name]

    def update_chart(self, data: list):
        self.ax.clear()

        if not data:
            self.ax.set_title("App Timeline")
            self.ax.set_axis_off()
            self.draw()
            return

        t0 = data[0][1]
        segments_by_app = {}
        for name, switched_at, duration in data:
            segments_by_app.setdefault(name, []).append((switched_at - t0, duration))

        apps = list(segments_by_app.keys())
        for i, app in enumerate(apps):
            self.ax.broken_barh(
                segments_by_app[app],
                (i - 0.4, 0.8),
                facecolors=self.get_color(app),
            )

        self.ax.set_yticks(range(len(apps)))
        self.ax.set_yticklabels(apps)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_title("App Timeline")
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.draw()

    def wheelEvent(self, event):
        event.ignore()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()