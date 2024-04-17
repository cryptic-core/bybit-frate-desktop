
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView

class TableWidget(QTableWidget):
    def __init__(self, parent=None):
        super(TableWidget, self).__init__(parent)
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels(["Symb", "SPOT", "PERP", "USD Value", "Ratio%", "Total Income",
                                        "8H Income", "Next Fund. APY", "Next Fund. Time"])
        self.setRowCount(5)
        self.resizeColumnsToContents()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)  # Hide the vertical header

    def update_table_data(self, data):
        self.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                item = QTableWidgetItem(value)
                self.setItem(i, j, item)
