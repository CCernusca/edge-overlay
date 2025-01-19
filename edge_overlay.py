import sys
import mss
import cv2
import time
import ctypes
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.BypassWindowManagerHint |
            Qt.WindowType.X11BypassWindowManagerHint |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, 1, 1)
        
        self.edges = []
        self.draw_empty = False
        self.fps = 0  # Variable to store FPS

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.draw_empty:
            # Draw the border rectangle
            pen = QPen(QColor(255, 0, 0, 128))  # Semi-transparent red
            pen.setWidth(5)
            painter.setPen(pen)
            painter.drawRect(self.rect())

            # Draw edges
            pen = QPen(QColor(0, 255, 0, 255))
            pen.setWidth(1)
            painter.setPen(pen)
            for edge in self.edges:
                x1, y1, x2, y2 = edge
                painter.drawLine(x1, y1, x2, y2)

        # Draw FPS
        font = QFont("Arial", 16)
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 255, 200))  # White color
        painter.drawText(10, 30, f"FPS: {self.fps:.1f}")

    def draw(self, show: bool = True):
        self.draw_empty = not show
        self.update()

tick_count = 0
last_time = time.time()

def main():
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    overlay.showFullScreen()

    # Create a QTimer to trigger a function every frame
    timer = QTimer(overlay)
    timer.timeout.connect(lambda: update(overlay))
    timer.start(int(1000 / 60))  # 60 FPS

    overlay.edges = detect_edges(overlay)
    
    sys.exit(app.exec())

def update(overlay: OverlayWindow | None = None):
    global tick_count, last_time

    current_time = time.time()
    elapsed_time = current_time - last_time

    if elapsed_time > 0:
        overlay.fps = 1 / elapsed_time  # Calculate FPS

    last_time = current_time

    overlay.edges = detect_edges(overlay)
    overlay.draw()

    tick_count += 1

def detect_edges(overlay: OverlayWindow | None = None) -> cv2.typing.MatLike:
    with mss.mss() as sct:
        hwnd = int(overlay.winId())
        user32 = ctypes.windll.user32

        user32.SetWindowDisplayAffinity(hwnd, 0x11)
        
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)

        user32.SetWindowDisplayAffinity(hwnd, 0x00)

        x_scale = screenshot.width / overlay.width()
        y_scale = screenshot.height / overlay.height()

        img = np.array(screenshot)
        combined_edges = np.zeros_like(img[:, :, 0])

        for i in range(3):
            channel = img[:, :, i]
            full_threshold = 50
            adjecant_threshold = 10
            edges = cv2.Canny(channel, adjecant_threshold, full_threshold)
            combined_edges = cv2.bitwise_or(combined_edges, edges)

        lines = cv2.HoughLinesP(combined_edges, 1, np.pi / 180, threshold=100, minLineLength=20, maxLineGap=0)

        adjusted_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                x1 /= x_scale
                y1 /= y_scale
                x2 /= x_scale
                y2 /= y_scale
                adjusted_lines.append((int(x1), int(y1), int(x2), int(y2)))

        filtered_lines = filter_duplicate_lines(adjusted_lines)
        return filtered_lines

def filter_duplicate_lines(lines, angle_threshold=5, distance_threshold=10):
    if not lines:
        return lines
    lines = sorted(lines, key=lambda line: line_length(line), reverse=True)

    filtered_lines = []
    for i, line1 in enumerate(lines):
        x1, y1, x2, y2 = line1
        rho1, theta1 = line_to_polar(x1, y1, x2, y2)
        is_duplicate = False
        for line2 in filtered_lines:
            x3, y3, x4, y4 = line2
            rho2, theta2 = line_to_polar(x3, y3, x4, y4)

            angle_diff = abs(theta1 - theta2)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            if angle_diff > angle_threshold:
                continue

            distance_diff = abs(rho1 - rho2)
            if distance_diff < distance_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            filtered_lines.append(line1)

    return filtered_lines

def line_length(line):
    x1, y1, x2, y2 = line
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def line_to_polar(x1, y1, x2, y2):
    theta = np.rad2deg(np.atan2(y2 - y1, x2 - x1)) % 360
    rho = abs((x2 - x1) * (-y1) - (y2 - y1) * (-x1)) / np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return rho, theta

if __name__ == "__main__":
    main()
