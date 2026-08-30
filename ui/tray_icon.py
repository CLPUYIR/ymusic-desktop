"""
System Tray Integration for YMusic Desktop.
Provides mini-player media controls, current track status, desktop notifications,
and background playback management when the main window is minimized or closed.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal, QObject
from ui.icons import IconFactory
from config import settings


class SystemTrayManager(QObject):
    """
    Manages the application system tray icon, context menu,
    and desktop notifications.
    """

    toggle_window_requested = pyqtSignal()
    play_pause_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    download_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(IconFactory.create_icon("app_logo", size=32))
        self.tray_icon.setToolTip("YMusic Desktop - Ready")

        self.current_title = "No media playing"
        self.current_artist = ""
        self.is_playing = False

        self._build_menu()
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _build_menu(self):
        """Constructs the system tray context menu."""
        self.menu = QMenu()

        # Track title / status header action (disabled as label)
        self.action_header = QAction(self.current_title, self.menu)
        self.action_header.setEnabled(False)
        self.menu.addAction(self.action_header)
        self.menu.addSeparator()

        # Playback control actions
        self.action_play_pause = QAction(IconFactory.create_icon("play"), "Play", self.menu)
        self.action_play_pause.triggered.connect(self.play_pause_requested.emit)
        self.menu.addAction(self.action_play_pause)

        self.action_next = QAction(IconFactory.create_icon("next"), "Next Track", self.menu)
        self.action_next.triggered.connect(self.next_requested.emit)
        self.menu.addAction(self.action_next)

        self.action_prev = QAction(IconFactory.create_icon("prev"), "Previous Track", self.menu)
        self.action_prev.triggered.connect(self.prev_requested.emit)
        self.menu.addAction(self.action_prev)

        self.menu.addSeparator()

        # Quick download action
        self.action_download = QAction(IconFactory.create_icon("download"), "Download Current Song", self.menu)
        self.action_download.triggered.connect(self.download_requested.emit)
        self.menu.addAction(self.action_download)

        self.menu.addSeparator()

        # Window visibility action
        self.action_toggle_window = QAction("Show / Hide Window", self.menu)
        self.action_toggle_window.triggered.connect(self.toggle_window_requested.emit)
        self.menu.addAction(self.action_toggle_window)

        # Quit action
        self.action_quit = QAction(IconFactory.create_icon("close"), "Quit YMusic", self.menu)
        self.action_quit.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(self.action_quit)

        self.tray_icon.setContextMenu(self.menu)

    def show(self):
        """Displays the tray icon."""
        self.tray_icon.show()

    def hide(self):
        """Hides the tray icon."""
        self.tray_icon.hide()

    def update_track_state(self, track_info: dict):
        """Updates tray menu label, tooltip, and triggers track notification."""
        title = track_info.get("title", "").strip() or "No media playing"
        artist = track_info.get("artist", "").strip()
        is_playing = track_info.get("is_playing", False)

        old_title = self.current_title
        self.current_title = title
        self.current_artist = artist
        self.is_playing = is_playing

        # Update header action
        header_text = f"🎵 {title}"
        if artist:
            header_text += f" - {artist}"
        self.action_header.setText(header_text[:45] + ("..." if len(header_text) > 45 else ""))

        # Update play/pause icon and text
        if is_playing:
            self.action_play_pause.setIcon(IconFactory.create_icon("pause"))
            self.action_play_pause.setText("Pause")
        else:
            self.action_play_pause.setIcon(IconFactory.create_icon("play"))
            self.action_play_pause.setText("Play")

        # Update tooltip
        self.tray_icon.setToolTip(f"YMusic: {title}" if title != "No media playing" else "YMusic Desktop")

        # Notify user of track change if window is minimized/hidden
        if settings.get("notifications_enabled", True) and title != "No media playing" and title != old_title:
            msg_body = artist if artist else "Playing on YMusic"
            self.tray_icon.showMessage(
                "Now Playing",
                f"{title}\n{msg_body}",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Handles user clicks on tray icon."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.toggle_window_requested.emit()
