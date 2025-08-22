import sys
import os
import time

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
    QFileDialog, QHBoxLayout, QShortcut
)
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QKeySequence

from snipping_tool import ScreenshotOverlay
from ocr_module import extract_text_from_image


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Text Extractor")
        self.setGeometry(100, 100, 900, 650)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Кнопки в верхней панели
        button_layout = QHBoxLayout()

        self.btn_screenshot = QPushButton("Aus Bild erkennen")
        self.btn_import = QPushButton("Aus Datei erkennen")
        self.btn_save = QPushButton("Aktuelle Konfiguration speichern")
        self.btn_toggle_edit = QPushButton("Bearbeiten: AUS (Ctrl+E)")

        self.btn_screenshot.clicked.connect(self.on_screenshot_click)
        self.btn_import.clicked.connect(self.on_import_click)
        self.btn_save.clicked.connect(self.on_save_click)
        self.btn_toggle_edit.clicked.connect(self.toggle_edit)

        button_layout.addWidget(self.btn_screenshot)
        button_layout.addWidget(self.btn_import)
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_toggle_edit)

        # Поле вывода текста
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)  # по умолчанию – только чтение
        self.text_output.setPlaceholderText("Es gibt noch keinen Text")

        # Горячие клавиши
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.toggle_edit)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.on_save_click)

        layout.addLayout(button_layout)
        layout.addWidget(self.text_output)

        self.setLayout(layout)

    # --- вспомогательное: безопасный показ/скрытие окна для скриншота ---
    def _hide_for_screenshot(self):
        # Спрятать окно и дать системе время обновить экран
        self.hide()
        QApplication.processEvents()
        QThread.msleep(120)  # короткая пауза ~120 мс (хватает, чтобы окно исчезло визуально)

    def _restore_after_screenshot(self):
        # Вернуть окно наверх
        self.show()
        self.raise_()
        self.activateWindow()
        QApplication.processEvents()

    # --- обработчики ---
    def on_screenshot_click(self):
        # спрятать окно, снять скрин, потом вернуть окно
        self._hide_for_screenshot()
        try:
            rect = ScreenshotOverlay.run_overlay()
        finally:
            self._restore_after_screenshot()

        if rect:
            self.text_output.setText("Erkennung läuft…")
            QApplication.processEvents()

            # предполагаем, что ScreenshotOverlay сохраняет в "screenshot.png"
            text_lines = extract_text_from_image("screenshot.png")
            self.text_output.setText("\n".join(text_lines))
        else:
            self.text_output.setText("Erkennung abgebrochen.")

    def on_import_click(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Bild auswählen", "", "Bilder (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.text_output.setText("Erkennung läuft…")
            QApplication.processEvents()

            text_lines = extract_text_from_image(file_path)
            self.text_output.setText("\n".join(text_lines))
        else:
            self.text_output.setText("Keine Datei ausgewählt.")

    def on_save_click(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Text speichern", "erkannt.txt", "Textdateien (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.text_output.toPlainText())
                self.text_output.append(f"\nGespeichert in: {file_path}")
            except Exception as e:
                self.text_output.append(f"\nFehler beim Speichern: {e!r}")
        else:
            self.text_output.append("\nSpeichern abgebrochen.")

    def toggle_edit(self):
        ro = self.text_output.isReadOnly()
        self.text_output.setReadOnly(not ro)
        self.btn_toggle_edit.setText("Bearbeiten: EIN (Ctrl+E)" if not ro else "Bearbeiten: AUS (Ctrl+E)")
        # курсор в конец текста при включении редактирования
        if not ro:
            cursor = self.text_output.textCursor()
            cursor.movePosition(cursor.End)
            self.text_output.setTextCursor(cursor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
