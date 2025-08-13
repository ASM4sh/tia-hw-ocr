import sys
import os
from PyQt5.QtWidgets import QWidget, QRubberBand
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QEventLoop
from PyQt5.QtGui import QGuiApplication, QPixmap, QPainter, QColor, QImage


class ScreenshotOverlay(QWidget):
    instances = []

    def __init__(self, screen, shared_result, loop):
        super().__init__()
        self.screen = screen
        self.shared_result = shared_result
        self.loop = loop

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(screen.geometry())

        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        ScreenshotOverlay.instances.append(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor(0, 0, 0, 50)  
        painter.fillRect(self.rect(), color)

    def mousePressEvent(self, event):
        self.origin = self.mapToGlobal(event.pos())
        self.rubberBand.setGeometry(QRect(event.pos(), QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        local_pos = event.pos()
        self.rubberBand.setGeometry(QRect(self.mapFromGlobal(self.origin), local_pos).normalized())

    def mouseReleaseEvent(self, event):
        self.rubberBand.hide()
        end_pos = self.mapToGlobal(event.pos())
        rect = QRect(self.origin, end_pos).normalized()

        for overlay in ScreenshotOverlay.instances:
            overlay.hide()

        QGuiApplication.processEvents()
        self.capture(rect)
        self.loop.quit()

    def capture(self, rect):    
        screens = QGuiApplication.screens()
        virtual_geometry = QGuiApplication.primaryScreen().virtualGeometry()

        combined_pixmap = QPixmap(virtual_geometry.size())
        combined_pixmap.fill(Qt.transparent)

        painter = QPainter(combined_pixmap)
        for screen in screens:
            geo = screen.geometry()
            screenshot = screen.grabWindow(0)
            top_left = geo.topLeft() - virtual_geometry.topLeft()
            painter.drawPixmap(top_left, screenshot)
        painter.end()

        offset_rect = rect.translated(-virtual_geometry.topLeft())
        cropped = combined_pixmap.copy(offset_rect)

        # Сохраняем как screenshot.png в папку с exe
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        save_path = os.path.join(exe_dir, "screenshot.png")
        cropped.save(save_path, "PNG")

        self.shared_result["image"] = cropped.toImage()

    @staticmethod
    def run_overlay():
        ScreenshotOverlay.instances = []
        app = QGuiApplication.instance()
        if app is None:
            app = QGuiApplication([])

        loop = QEventLoop()
        shared_result = {}

        for screen in QGuiApplication.screens():
            overlay = ScreenshotOverlay(screen, shared_result, loop)
            overlay.showFullScreen()

        loop.exec_()
        return shared_result.get("image", None)