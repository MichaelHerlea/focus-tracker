from PyQt6.QtWidgets import * # type: ignore
from ForegroundApplicationTracker import ForegroundApplicationTracker
from ApplicationSpecificData import ApplicationSpecificData

class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.application_tracker = ForegroundApplicationTracker()

        self.setWindowTitle("Test123")

        main_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        start_button = QPushButton("Start")
        start_button.clicked.connect(self.on_start_button_clicked)
        row1.addWidget(start_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.on_stop_button_clicked)
        row1.addWidget(stop_button)
        main_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.output_label = QLabel("Output")
        row2.addWidget(self.output_label)
        main_layout.addLayout(row2)

        self.setLayout(main_layout)
    
    def on_start_button_clicked(self):
        self.application_tracker.start()
    
    def on_stop_button_clicked(self):
        self.application_tracker.stop()
        self.output_label.setText(ApplicationSpecificData.get_all_instances_to_string())

app = QApplication([])
window = MainWindow()
window.show()
app.exec()