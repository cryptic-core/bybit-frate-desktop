
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView

class TableWidget(QTableWidget):
    def __init__(self, parent=None):
        super(TableWidget, self).__init__(parent)
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels(["Symb", "SPOT", "PERP", "USD Value", "Ratio%", "Total Income",
                                        "8H Income", "Next Fund. APY", "Next Fund. Time"])
        self.setRowCount(5)  # Example: 5 rows

        symb_data = [
            ["BTC", "50000", "50500", "500000", "1.5", "10000", "500", "10%", "2024-04-03 12:00:00"],
            ["ETH", "2500", "2600", "20000", "2.2", "800", "40", "8%", "2024-04-03 12:00:00"],
            ["XRP", "1.5", "1.55", "150", "1.8", "10", "1", "12%", "2024-04-03 12:00:00"],
            ["LTC", "300", "310", "3000", "1.7", "100", "5", "9%", "2024-04-03 12:00:00"],
            ["ADA", "1.2", "1.25", "10", "1.9", "1", "0.1", "15%", "2024-04-03 12:00:00"]
        ]
        self.resizeColumnsToContents()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)  # Hide the vertical header

    def update_table_data(self, data):
        self.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                item = QTableWidgetItem(value)
                self.setItem(i, j, item)
