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
from backend.moda import calculate_mvp_rankings, DEFAULT_WEIGHTS, calculate_advanced_stats
from backend.data_fetcher import fetch_player_data
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

        # --- Button ---
        self.showStatsButton = QPushButton('Show Player Stats')
        self.showStatsButton.clicked.connect(self.show_player_stats)
        mainLayout.addWidget(self.showStatsButton)

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

        # --- Calculate MVP Button ---
        self.calculateButton = QPushButton('Calculate MVP')
        self.calculateButton.clicked.connect(self.calculate_mvp)
        mainLayout.addWidget(self.calculateButton)

        # --- Table ---
        self.tableWidget = QTableWidget()
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Make table read-only
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Make columns fill available space
        mainLayout.addWidget(self.tableWidget)

    @pyqtSlot(str, int, QLabel)
    def update_weight(self, name, value, label):
        self.weights[name] = value
        label.setText(f"{name}: {value}")

    @pyqtSlot()
    def show_player_stats(self):
        try:
            # Fetch player data and calculate advanced stats
            player_stats = fetch_player_data()
            df = calculate_advanced_stats(player_stats)

            # Filter columns
            columns_to_keep = list(DEFAULT_WEIGHTS.keys())
            if 'name' in df.columns:
                columns_to_keep.append('name')
            try:
                df = df[columns_to_keep]
            except KeyError as e:
                print(f"Warning: One or more columns from DEFAULT_WEIGHTS not found in DataFrame: {e}")
                existing_columns = [col for col in columns_to_keep if col in df.columns]
                df = df[existing_columns]

            # Set up the table
            self.tableWidget.clear()
            self.tableWidget.setRowCount(df.shape[0])
            self.tableWidget.setColumnCount(df.shape[1])
            self.tableWidget.setHorizontalHeaderLabels(df.columns.tolist())

            # Populate the table
            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    item = QTableWidgetItem(str(df.iloc[i, j]))
                    self.tableWidget.setItem(i, j, item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}\n\n{traceback.format_exc()}")

    @pyqtSlot()
    def calculate_mvp(self):
        try:
            mvp_rankings = calculate_mvp_rankings(self.weights)

            self.tableWidget.clear()
            self.tableWidget.setRowCount(len(mvp_rankings))
            self.tableWidget.setColumnCount(3)
            self.tableWidget.setHorizontalHeaderLabels(['Rank', 'Player', 'MVP Score'])

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