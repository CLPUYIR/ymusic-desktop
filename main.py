"""
YMusic Desktop - Entry Point & Application Lifecycle.
A dedicated lightweight, ad-free desktop client for YouTube and YouTube Music
with background playback, media controls, and yt-dlp downloader integration.
"""

import sys
import os
import argparse

# ----------------- Chromium Flags for Background Audio ----------------- #
# Crucial: Must be set BEFORE QApplication initialization to prevent Chromium
# from throttling or pausing audio playback when minimized or hidden in tray.
CHROMIUM_FLAGS = (
    "--disable-background-timer-throttling "
    "--disable-renderer-backgrounding "
    "--disable-backgrounding-occluded-windows "
    "--autoplay-policy=no-user-gesture-required "
    "--enable-features=AudioServiceOutOfProcess "
    "--enable-gpu-rasterization"
)

existing_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"{existing_flags} {CHROMIUM_FLAGS}".strip()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from config import settings, Config
from ui.styles import DARK_THEME_QSS
from ui.main_window import MainWindow


def parse_arguments():
    """Parses CLI arguments."""
    parser = argparse.ArgumentParser(description="YMusic Desktop Client")
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Start the application minimized to the system tray",
    )
    parser.add_argument(
        "--service",
        choices=["music", "youtube"],
        default=None,
        help="Choose startup service (music or youtube)",
    )
    return parser.parse_args()


def main():
    # Parse CLI flags
    args = parse_arguments()

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName(Config.APP_NAME)
    app.setOrganizationName(Config.APP_ORG)
    app.setApplicationVersion(Config.APP_VERSION)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # Apply modern dark stylesheet
    app.setStyleSheet(DARK_THEME_QSS)

    # Override startup service if provided
    if args.service:
        settings.set("default_service", args.service)

    # Initialize Main Window
    window = MainWindow()

    # Check startup state
    start_min = args.minimized or settings.get("start_minimized", False)
    if start_min:
        window.hide()
        if settings.get("notifications_enabled", True):
            window.tray_mgr.tray_icon.showMessage(
                "YMusic Desktop",
                "Started in background (System Tray).",
                window.windowIcon(),
                2000,
            )
    else:
        window.show()
        window.raise_()
        window.activateWindow()

    # Execute Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
