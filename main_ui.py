import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
    QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import Qt

from snipping_tool import ScreenshotOverlay
from ocr_module import extract_text_from_image

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Text Extractor")
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Кнопки в верхней панели
        button_layout = QHBoxLayout()

        self.btn_screenshot = QPushButton("Распознать с изображения")
        self.btn_import = QPushButton("Экспортировать из файла")
        self.btn_save = QPushButton("Сохранить текущее")

        self.btn_screenshot.clicked.connect(self.on_screenshot_click)
        self.btn_import.clicked.connect(self.on_import_click)
        self.btn_save.clicked.connect(self.on_save_click)

        button_layout.addWidget(self.btn_screenshot)
        button_layout.addWidget(self.btn_import)
        button_layout.addWidget(self.btn_save)

        # Поле вывода текста
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setPlaceholderText("Текст отсутствует")

        layout.addLayout(button_layout)
        layout.addWidget(self.text_output)

        self.setLayout(layout)

    def on_screenshot_click(self):
        rect = ScreenshotOverlay.run_overlay()
        if rect:
            self.text_output.setText("Распознаём текст...")
            QApplication.processEvents()

            text_lines = extract_text_from_image("screenshot.png")
            self.text_output.setText("\n".join(text_lines))
        else:
            self.text_output.setText("Скриншот не был сделан.")

    def on_import_click(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбери изображение", "", "Изображения (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.text_output.setText("Распознаём текст из файла...")
            QApplication.processEvents()

            text_lines = extract_text_from_image(file_path)
            self.text_output.setText("\n".join(text_lines))
        else:
            self.text_output.setText("Файл не выбран.")

    def on_save_click(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить текст", "распознанный_текст.txt", "Текстовые файлы (*.txt)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_output.toPlainText())
            self.text_output.append(f"\nТекст сохранён в: {file_path}")
        else:
            self.text_output.append("\nСохранение отменено.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())