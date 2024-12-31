import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from backend.moda import calculate_mvp_rankings, DEFAULT_WEIGHTS
import traceback

class MVPApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('NBA MVP Ranking')

        # Initialize weights (you can load from a config file if needed)
        self.weights = DEFAULT_WEIGHTS.copy()

        self.initUI()

    def initUI(self):
        # --- Layout ---
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        # --- Sliders ---
        slidersLayout = QHBoxLayout()
        mainLayout.addLayout(slidersLayout)

        self.sliders = {}
        for name, value in self.weights.items():
            sliderBox = QVBoxLayout()
            label = QLabel(f"{name}: {value}")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(value)
            slider.valueChanged.connect(lambda value, name=name, label=label: self.update_weight(name, value, label))

            self.sliders[name] = slider
            sliderBox.addWidget(label)
            sliderBox.addWidget(slider)
            slidersLayout.addLayout(sliderBox)

        # --- Button ---
        self.calculateButton = QPushButton('Calculate MVP')
        self.calculateButton.clicked.connect(self.calculate_mvp)
        mainLayout.addWidget(self.calculateButton)

        # --- Table ---
        self.tableWidget = QTableWidget()
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Make table read-only
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(['Rank', 'Player', 'MVP Score'])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Make columns fill available space
        mainLayout.addWidget(self.tableWidget)

    @pyqtSlot(str, int, QLabel)
    def update_weight(self, name, value, label):
        self.weights[name] = value
        label.setText(f"{name}: {value}")

    @pyqtSlot()
    def calculate_mvp(self):
        try:
            mvp_rankings = calculate_mvp_rankings(self.weights)

            self.tableWidget.setRowCount(len(mvp_rankings))
            for i, player_data in enumerate(mvp_rankings):
                self.tableWidget.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.tableWidget.setItem(i, 1, QTableWidgetItem(player_data['name']))
                self.tableWidget.setItem(i, 2, QTableWidgetItem(str(round(player_data['MVP Score'], 2))))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}\n\n{traceback.format_exc()}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MVPApp()
    ex.show()
    sys.exit(app.exec())