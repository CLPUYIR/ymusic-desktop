"""
Main Application Window for YMusic Desktop.
Coordinates persistent dual-tab WebEngine views (YouTube Music & YouTube Video),
Media Controller, System Tray, Ad Blocker, and Downloader.
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolBar,
    QLineEdit,
    QPushButton,
    QToolButton,
    QLabel,
    QSlider,
    QStatusBar,
    QDialog,
    QFormLayout,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QButtonGroup,
    QStackedWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QCloseEvent, QWindowStateChangeEvent

from config import settings, Config
from core.adblocker import AdBlockUrlRequestInterceptor, create_adblock_script
from core.web_page import YMusicWebPage
from core.media_controller import MediaController
from core.downloader import download_manager
from ui.icons import IconFactory
from ui.tray_icon import SystemTrayManager
from ui.download_dialog import QuickDownloadDialog, DownloadManagerWindow


class SettingsDialog(QDialog):
    """Configuration dialog for application preferences."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences - YMusic Desktop")
        self.resize(460, 340)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        form = QFormLayout()
        form.setSpacing(12)

        # Default Service
        self.combo_service = QComboBox()
        self.combo_service.addItem("YouTube Music", "music")
        self.combo_service.addItem("Standard YouTube", "youtube")
        current_svc = settings.get("default_service", "music")
        self.combo_service.setCurrentIndex(0 if current_svc == "music" else 1)
        form.addRow("Default Startup View:", self.combo_service)

        # Download Directory
        dir_layout = QHBoxLayout()
        self.txt_dir = QLineEdit(settings.get("download_dir"))
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_dir)
        dir_layout.addWidget(self.txt_dir)
        dir_layout.addWidget(btn_browse)
        form.addRow("Download Folder:", dir_layout)

        # Checkboxes
        self.chk_adblock = QCheckBox("Enable Network Ad-Blocking & Auto-Skip")
        self.chk_adblock.setChecked(settings.get("adblock_enabled", True))
        form.addRow("", self.chk_adblock)

        self.chk_close_tray = QCheckBox("Minimize to System Tray on Close (X)")
        self.chk_close_tray.setChecked(settings.get("close_to_tray", True))
        form.addRow("", self.chk_close_tray)

        self.chk_min_tray = QCheckBox("Minimize to Tray on Minimize (_)")
        self.chk_min_tray.setChecked(settings.get("minimize_to_tray", True))
        form.addRow("", self.chk_min_tray)

        self.chk_notif = QCheckBox("Show Desktop Notifications on Track Change")
        self.chk_notif.setChecked(settings.get("notifications_enabled", True))
        form.addRow("", self.chk_notif)

        layout.addLayout(form)
        layout.addStretch()

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("background-color: #ff0033; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save_settings)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _browse_dir(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Folder", self.txt_dir.text())
        if chosen:
            self.txt_dir.setText(chosen)

    def _save_settings(self):
        settings.set("default_service", self.combo_service.currentData())
        settings.set("download_dir", self.txt_dir.text().strip())
        settings.set("adblock_enabled", self.chk_adblock.isChecked())
        settings.set("close_to_tray", self.chk_close_tray.isChecked())
        settings.set("minimize_to_tray", self.chk_min_tray.isChecked())
        settings.set("notifications_enabled", self.chk_notif.isChecked())
        self.accept()


class MainWindow(QMainWindow):
    """
    Main Application Window integrating persistent dual-views, Media Controls, and Downloader.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YMusic Desktop")
        self.resize(1200, 800)
        self.setWindowIcon(IconFactory.create_icon("app_logo", size=64))

        # Setup Profile, Interceptor, and Pages
        self._init_web_engine()

        # Setup Media Controller targeting active web view page
        self.media_ctrl = MediaController(self._get_active_page, self)

        # Setup System Tray
        self.tray_mgr = SystemTrayManager(self)

        # Setup UI (Dual persistent WebViews in QStackedWidget)
        self._init_ui()
        self._connect_signals()

        # Show tray icon
        self.tray_mgr.show()

    def _get_active_page(self):
        """Returns the page of currently active or playing web view."""
        if hasattr(self, "stacked_views"):
            cur_view = self.stacked_views.currentWidget()
            if isinstance(cur_view, QWebEngineView):
                return cur_view.page()
        return None

    def _init_web_engine(self):
        """Configures WebEngine profile and custom request interceptor."""
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent(settings.USER_AGENT)

        # Install AdBlock Request Interceptor
        self.adblock_interceptor = AdBlockUrlRequestInterceptor(
            enabled=settings.get("adblock_enabled", True)
        )
        self.profile.setUrlRequestInterceptor(self.adblock_interceptor)

        # Insert DOM AdBlock script
        self.profile.scripts().insert(create_adblock_script())

    def _init_ui(self):
        """Constructs window widgets, toolbars, dual-view stack, and player bar."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------- Top Navigation Toolbar ----------------- #
        self.nav_toolbar = QToolBar("Navigation", self)
        self.nav_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.nav_toolbar)

        # Back / Forward / Refresh
        self.btn_back = QToolButton()
        self.btn_back.setIcon(IconFactory.create_icon("back"))
        self.btn_back.setToolTip("Go Back")
        self.btn_back.clicked.connect(self._go_back)

        self.btn_fwd = QToolButton()
        self.btn_fwd.setIcon(IconFactory.create_icon("forward"))
        self.btn_fwd.setToolTip("Go Forward")
        self.btn_fwd.clicked.connect(self._go_forward)

        self.btn_reload = QToolButton()
        self.btn_reload.setIcon(IconFactory.create_icon("refresh"))
        self.btn_reload.setToolTip("Reload Page")
        self.btn_reload.clicked.connect(self._reload_page)

        self.nav_toolbar.addWidget(self.btn_back)
        self.nav_toolbar.addWidget(self.btn_fwd)
        self.nav_toolbar.addWidget(self.btn_reload)
        self.nav_toolbar.addSeparator()

        # Service Switcher (YouTube Music vs YouTube Video)
        self.btn_mode_music = QToolButton()
        self.btn_mode_music.setIcon(IconFactory.create_icon("music"))
        self.btn_mode_music.setText(" YouTube Music")
        self.btn_mode_music.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_mode_music.setCheckable(True)
        self.btn_mode_music.clicked.connect(self.switch_to_music)

        self.btn_mode_yt = QToolButton()
        self.btn_mode_yt.setIcon(IconFactory.create_icon("youtube"))
        self.btn_mode_yt.setText(" YouTube Video")
        self.btn_mode_yt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_mode_yt.setCheckable(True)
        self.btn_mode_yt.clicked.connect(self.switch_to_youtube)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.btn_mode_music)
        self.mode_group.addButton(self.btn_mode_yt)

        self.nav_toolbar.addWidget(self.btn_mode_music)
        self.nav_toolbar.addWidget(self.btn_mode_yt)
        self.nav_toolbar.addSeparator()

        # URL / Search Bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search songs, artists, or paste YouTube link...")
        self.url_bar.returnPressed.connect(self._on_search_or_navigate)
        self.nav_toolbar.addWidget(self.url_bar)

        # AdBlock Shield Badge
        self.btn_shield = QToolButton()
        self.btn_shield.setIcon(IconFactory.create_icon("shield", IconFactory.SUCCESS_COLOR))
        self.btn_shield.setToolTip("Ad Blocker Active (Click to toggle)")
        self.btn_shield.clicked.connect(self._toggle_adblock)
        self.nav_toolbar.addWidget(self.btn_shield)

        # Download Current Song Button (Vibrant)
        self.btn_download_cur = QPushButton(" ⬇ Download")
        self.btn_download_cur.setIcon(IconFactory.create_icon("download"))
        self.btn_download_cur.setStyleSheet(
            "background-color: #ff0033; color: #ffffff; font-weight: bold; border-radius: 6px; padding: 6px 14px;"
        )
        self.btn_download_cur.setToolTip("Download currently playing audio or video")
        self.btn_download_cur.clicked.connect(self.open_quick_download)
        self.nav_toolbar.addWidget(self.btn_download_cur)

        # Download Manager Button
        self.btn_dl_manager = QToolButton()
        self.btn_dl_manager.setIcon(IconFactory.create_icon("folder"))
        self.btn_dl_manager.setToolTip("Open Download Manager")
        self.btn_dl_manager.clicked.connect(self.open_download_manager)
        self.nav_toolbar.addWidget(self.btn_dl_manager)

        # Settings Button
        self.btn_settings = QToolButton()
        self.btn_settings.setIcon(IconFactory.create_icon("settings"))
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        self.nav_toolbar.addWidget(self.btn_settings)

        # ----------------- Stacked Persistent WebViews ----------------- #
        self.stacked_views = QStackedWidget(self)

        # 1. YouTube Music View
        self.view_music = QWebEngineView(self)
        self.page_music = YMusicWebPage(self.profile, self.view_music)
        self.view_music.setPage(self.page_music)
        self.view_music.setUrl(QUrl(Config.URL_YOUTUBE_MUSIC))

        # 2. Standard YouTube View
        self.view_yt = QWebEngineView(self)
        self.page_yt = YMusicWebPage(self.profile, self.view_yt)
        self.view_yt.setPage(self.page_yt)
        self.view_yt.setUrl(QUrl(Config.URL_YOUTUBE))

        self.stacked_views.addWidget(self.view_music)
        self.stacked_views.addWidget(self.view_yt)
        main_layout.addWidget(self.stacked_views, 1)

        # ----------------- Bottom Status & Mini Player Bar ----------------- #
        self.bottom_player = QWidget(self)
        self.bottom_player.setStyleSheet("background-color: #121212; border-top: 1px solid #222222; padding: 4px;")
        bottom_layout = QHBoxLayout(self.bottom_player)
        bottom_layout.setContentsMargins(12, 4, 12, 4)
        bottom_layout.setSpacing(12)

        # Mini Media Controls
        self.btn_mini_prev = QToolButton()
        self.btn_mini_prev.setIcon(IconFactory.create_icon("prev", size=24))
        self.btn_mini_prev.clicked.connect(self.media_ctrl.previous_track)

        self.btn_mini_play = QToolButton()
        self.btn_mini_play.setIcon(IconFactory.create_icon("play", size=24))
        self.btn_mini_play.clicked.connect(self.media_ctrl.play_pause)

        self.btn_mini_next = QToolButton()
        self.btn_mini_next.setIcon(IconFactory.create_icon("next", size=24))
        self.btn_mini_next.clicked.connect(self.media_ctrl.next_track)

        bottom_layout.addWidget(self.btn_mini_prev)
        bottom_layout.addWidget(self.btn_mini_play)
        bottom_layout.addWidget(self.btn_mini_next)

        # Track Info Label
        self.lbl_current_track = QLabel("Ready • YouTube Music")
        self.lbl_current_track.setStyleSheet("color: #ffffff; font-weight: bold;")
        bottom_layout.addWidget(self.lbl_current_track, 1)

        # Adblock status counter
        self.lbl_ad_counter = QLabel("🛡️ Ads Blocked: 0")
        self.lbl_ad_counter.setStyleSheet("color: #888888; font-size: 11px;")
        bottom_layout.addWidget(self.lbl_ad_counter)

        # Volume Slider
        vol_icon = QLabel("🔊")
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(settings.get("volume", 100))
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.valueChanged.connect(self.media_ctrl.set_volume)

        bottom_layout.addWidget(vol_icon)
        bottom_layout.addWidget(self.vol_slider)

        main_layout.addWidget(self.bottom_player, 0)

        # Manager dialog instance
        self.download_manager_window = DownloadManagerWindow(self)

        # Initial view selection
        initial_service = settings.get("default_service", "music")
        if initial_service == "youtube":
            self.switch_to_youtube()
        else:
            self.switch_to_music()

    def _connect_signals(self):
        """Connects WebEngine, Media Controller, and Tray signals."""
        self.view_music.urlChanged.connect(self._on_music_url_changed)
        self.view_yt.urlChanged.connect(self._on_yt_url_changed)

        self.view_music.titleChanged.connect(self._on_music_title_changed)
        self.view_yt.titleChanged.connect(self._on_yt_title_changed)

        # Media controller signals
        self.media_ctrl.track_changed.connect(self._on_track_changed)
        self.media_ctrl.playback_state_changed.connect(self._on_playback_state_changed)

        # Tray signals
        self.tray_mgr.toggle_window_requested.connect(self.toggle_window_visibility)
        self.tray_mgr.play_pause_requested.connect(self.media_ctrl.play_pause)
        self.tray_mgr.next_requested.connect(self.media_ctrl.next_track)
        self.tray_mgr.prev_requested.connect(self.media_ctrl.previous_track)
        self.tray_mgr.download_requested.connect(self.open_quick_download)
        self.tray_mgr.quit_requested.connect(self.force_quit)

        # Downloader signals
        download_manager.task_completed.connect(self._on_download_finished)

    # ----------------- Persistent View Switching ----------------- #

    def switch_to_music(self):
        """Switches display to YouTube Music view without reloading or resetting."""
        self.btn_mode_music.setChecked(True)
        self.stacked_views.setCurrentWidget(self.view_music)
        self.url_bar.setText(self.view_music.url().toString())
        self.media_ctrl.update_track_info()

    def switch_to_youtube(self):
        """Switches display to Standard YouTube view without reloading or resetting."""
        self.btn_mode_yt.setChecked(True)
        self.stacked_views.setCurrentWidget(self.view_yt)
        self.url_bar.setText(self.view_yt.url().toString())
        self.media_ctrl.update_track_info()

    def _get_current_view(self) -> QWebEngineView:
        return self.stacked_views.currentWidget()

    def _go_back(self):
        self._get_current_view().back()

    def _go_forward(self):
        self._get_current_view().forward()

    def _reload_page(self):
        self._get_current_view().reload()

    def _on_search_or_navigate(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        cur_view = self._get_current_view()
        if text.startswith("http://") or text.startswith("https://"):
            cur_view.setUrl(QUrl(text))
        else:
            if cur_view == self.view_music:
                search_url = f"https://music.youtube.com/search?q={QUrl.toPercentEncoding(text).data().decode()}"
            else:
                search_url = f"https://www.youtube.com/results?search_query={QUrl.toPercentEncoding(text).data().decode()}"
            cur_view.setUrl(QUrl(search_url))

    def _on_music_url_changed(self, url: QUrl):
        if self._get_current_view() == self.view_music:
            self.url_bar.setText(url.toString())

    def _on_yt_url_changed(self, url: QUrl):
        if self._get_current_view() == self.view_yt:
            self.url_bar.setText(url.toString())

    def _on_music_title_changed(self, title: str):
        if self._get_current_view() == self.view_music and title:
            self.setWindowTitle(f"{title} - YMusic")

    def _on_yt_title_changed(self, title: str):
        if self._get_current_view() == self.view_yt and title:
            self.setWindowTitle(f"{title} - YMusic")

    # ----------------- Media & Track Updates ----------------- #

    def _on_track_changed(self, track_data: dict):
        title = track_data.get("title", "").strip()
        artist = track_data.get("artist", "").strip()
        duration = track_data.get("duration", "0:00")
        current_time = track_data.get("current_time", "0:00")

        if title:
            display_str = f"🎵 {title}"
            if artist:
                display_str += f" — {artist}"
            display_str += f"  [{current_time} / {duration}]"
            self.lbl_current_track.setText(display_str)
        else:
            active_name = "YouTube Music" if self._get_current_view() == self.view_music else "YouTube Video"
            self.lbl_current_track.setText(f"Ready • {active_name}")

        # Update ad counter
        self.lbl_ad_counter.setText(f"🛡️ Ads Blocked: {self.adblock_interceptor.blocked_count}")

        # Update Tray
        self.tray_mgr.update_track_state(track_data)

    def _on_playback_state_changed(self, is_playing: bool):
        if is_playing:
            self.btn_mini_play.setIcon(IconFactory.create_icon("pause", size=24))
        else:
            self.btn_mini_play.setIcon(IconFactory.create_icon("play", size=24))

    # ----------------- Downloader & Dialogs ----------------- #

    def open_quick_download(self):
        """Opens quick download modal for the currently active video/track."""
        cur_view = self._get_current_view()
        cur_url = cur_view.url().toString()
        title = self.media_ctrl.current_track.get("title", "")
        
        dialog = QuickDownloadDialog(current_url=cur_url, default_title=title, parent=self)
        dialog.download_started.connect(lambda task_id: self.statusBar().showMessage(f"Download started...", 4000))
        dialog.exec()

    def open_download_manager(self):
        """Opens the full download manager."""
        self.download_manager_window.show()
        self.download_manager_window.raise_()
        self.download_manager_window.activateWindow()

    def open_settings(self):
        """Opens settings dialog."""
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.adblock_interceptor.set_enabled(settings.get("adblock_enabled", True))
            self._update_shield_icon()

    def _toggle_adblock(self):
        cur = settings.get("adblock_enabled", True)
        settings.set("adblock_enabled", not cur)
        self.adblock_interceptor.set_enabled(not cur)
        self._update_shield_icon()
        self.statusBar().showMessage(f"Ad-blocker {'enabled' if not cur else 'disabled'}.", 3000)

    def _update_shield_icon(self):
        enabled = settings.get("adblock_enabled", True)
        color = IconFactory.SUCCESS_COLOR if enabled else IconFactory.MUTED_COLOR
        self.btn_shield.setIcon(IconFactory.create_icon("shield", color))
        self.btn_shield.setToolTip(f"Ad Blocker {'Active' if enabled else 'Disabled'} (Click to toggle)")

    def _on_download_finished(self, task_id: str, filepath: str, success: bool, err_msg: str):
        if success:
            filename = os.path.basename(filepath)
            self.statusBar().showMessage(f"✓ Download complete: {filename}", 6000)
            if settings.get("notifications_enabled", True):
                self.tray_mgr.tray_icon.showMessage(
                    "Download Complete",
                    f"Saved: {filename}",
                    QIcon(IconFactory.create_icon("download")),
                    3000,
                )
        else:
            self.statusBar().showMessage(f"✕ Download failed: {err_msg[:50]}", 6000)

    # ----------------- Window & Tray Visibility ----------------- #

    def toggle_window_visibility(self):
        """Toggles between showing and hiding the main window."""
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()
            self.raise_()

    def changeEvent(self, event):
        """Handles minimize events to hide to system tray if configured."""
        if event.type() == QWindowStateChangeEvent.Type.WindowStateChange:
            if self.isMinimized() and settings.get("minimize_to_tray", True):
                self.hide()
                event.accept()
                return
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent):
        """Intercepts close button (X) to minimize to tray instead of quitting."""
        if settings.get("close_to_tray", True):
            event.ignore()
            self.hide()
            if settings.get("notifications_enabled", True):
                self.tray_mgr.tray_icon.showMessage(
                    "YMusic Desktop",
                    "Application is running in the background.",
                    QIcon(IconFactory.create_icon("app_logo")),
                    2000,
                )
        else:
            self.force_quit()

    def force_quit(self):
        """Completely terminates the application."""
        self.tray_mgr.hide()
        self.close()
        import sys
        sys.exit(0)
