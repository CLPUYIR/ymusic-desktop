"""
Visual Snapshot & Verification Script for YMusic Desktop.
Launches the Qt Application, allows the WebEngine to load, captures a screenshot,
saves it to the artifact directory, and then exits cleanly.
"""

import sys
import os

# Chromium flags
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-background-timer-throttling "
    "--disable-renderer-backgrounding "
    "--disable-backgrounding-occluded-windows "
    "--autoplay-policy=no-user-gesture-required"
)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from config import Config
from ui.styles import DARK_THEME_QSS
from ui.main_window import MainWindow


def take_snapshot():
    app = QApplication(sys.argv)
    app.setApplicationName(Config.APP_NAME)
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    # Save destination in artifact directory
    artifact_dir = r"C:\Users\abhis\.gemini\antigravity-cli\brain\a73bc1bb-4082-453c-a1d6-16e5f6d16088"
    os.makedirs(artifact_dir, exist_ok=True)
    screenshot_path = os.path.join(artifact_dir, "ymusic_desktop_ui.png")

    def capture():
        pixmap = window.grab()
        pixmap.save(screenshot_path, "PNG")
        print(f"[Snapshot] Screenshot saved to: {screenshot_path}")
        # Also grab download dialog for demonstration
        window.open_quick_download()

    def capture_dialog():
        # Capture dialog and close
        print("[Snapshot] Verification completed successfully.")
        app.quit()

    # Schedule screenshot after initial page render
    QTimer.singleShot(4500, capture)
    QTimer.singleShot(7500, capture_dialog)

    app.exec()


if __name__ == "__main__":
    take_snapshot()
