"""
Main Application Window for YMusic Desktop.
Coordinates persistent dual-tab WebEngine views (YouTube Music & YouTube Video),
Media Controller, System Tray, Ad Blocker, and Downloader.
"""

import os
from pathlib import Path
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
    QTabWidget,
    QMenu,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineSettings,
    QWebEngineScript,
    QWebEngineUrlRequestInterceptor,
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QCloseEvent, QWindowStateChangeEvent, QKeySequence, QShortcut

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

        self.chk_auto_pause = QCheckBox("Auto-pause Audio on Inactive Tabs when Switching")
        self.chk_auto_pause.setChecked(settings.get("auto_pause_inactive_tabs", True))
        form.addRow("", self.chk_auto_pause)

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
        download_dir = self.txt_dir.text().strip()
        if download_dir:
            try:
                Path(download_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"[Settings] Error creating download directory: {e}")
        settings.set("default_service", self.combo_service.currentData())
        settings.set("download_dir", download_dir)
        settings.set("adblock_enabled", self.chk_adblock.isChecked())
        settings.set("close_to_tray", self.chk_close_tray.isChecked())
        settings.set("minimize_to_tray", self.chk_min_tray.isChecked())
        settings.set("notifications_enabled", self.chk_notif.isChecked())
        settings.set("auto_pause_inactive_tabs", self.chk_auto_pause.isChecked())
        self.accept()


class MainWindow(QMainWindow):
    """
    Main Application Window integrating dynamic multi-tab WebEngine views
    (YouTube Music & YouTube Video), Media Controls, System Tray, and Downloader.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YMusic Desktop")
        self.resize(1200, 800)
        self.setWindowIcon(IconFactory.create_icon("app_logo", size=64))

        # Setup Profile and Ad-Block Interceptor
        self._init_web_engine()

        # Setup Media Controller targeting active web view page
        self.media_ctrl = MediaController(self._get_active_page, self)

        # Setup UI (Multi-Tab QTabWidget)
        self._init_ui()

        # Setup System Tray
        self.tray_mgr = SystemTrayManager(self)

        # Setup Keyboard Shortcuts
        self._setup_shortcuts()

        # Connect signals
        self._connect_signals()

        # Create initial tab based on default preference
        initial_service = settings.get("default_service", "music")
        self.create_new_tab(service=initial_service, switch_to=True)

        # Show tray icon
        self.tray_mgr.show()

    def _get_active_page(self):
        """Returns the page of currently active web view tab."""
        view = self._get_current_view()
        return view.page() if view else None

    def _get_current_view(self) -> QWebEngineView:
        """Returns the currently active QWebEngineView."""
        if hasattr(self, "tabs"):
            widget = self.tabs.currentWidget()
            if isinstance(widget, QWebEngineView):
                return widget
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
        """Constructs window widgets, toolbars, multi-tab bar, and player bar."""
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
        self.btn_back.setToolTip("Go Back (Alt+Left)")
        self.btn_back.clicked.connect(self._go_back)

        self.btn_fwd = QToolButton()
        self.btn_fwd.setIcon(IconFactory.create_icon("forward"))
        self.btn_fwd.setToolTip("Go Forward (Alt+Right)")
        self.btn_fwd.clicked.connect(self._go_forward)

        self.btn_reload = QToolButton()
        self.btn_reload.setIcon(IconFactory.create_icon("refresh"))
        self.btn_reload.setToolTip("Reload Page (F5)")
        self.btn_reload.clicked.connect(self._reload_page)

        self.nav_toolbar.addWidget(self.btn_back)
        self.nav_toolbar.addWidget(self.btn_fwd)
        self.nav_toolbar.addWidget(self.btn_reload)
        self.nav_toolbar.addSeparator()

        # Fast New Tab Launchers (YouTube Music & Standard YouTube)
        self.btn_add_music = QToolButton()
        self.btn_add_music.setIcon(IconFactory.create_icon("music"))
        self.btn_add_music.setText(" + Music")
        self.btn_add_music.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_add_music.setToolTip("Open New YouTube Music Tab (Ctrl+T / Ctrl+M)")
        self.btn_add_music.clicked.connect(lambda: self.create_new_tab("music", switch_to=True))

        self.btn_add_yt = QToolButton()
        self.btn_add_yt.setIcon(IconFactory.create_icon("youtube"))
        self.btn_add_yt.setText(" + YouTube")
        self.btn_add_yt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_add_yt.setToolTip("Open New YouTube Video Tab (Ctrl+Y)")
        self.btn_add_yt.clicked.connect(lambda: self.create_new_tab("youtube", switch_to=True))

        self.nav_toolbar.addWidget(self.btn_add_music)
        self.nav_toolbar.addWidget(self.btn_add_yt)
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

        # Download Current Song Button
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

        # ----------------- Dynamic Multi-Tab Bar (QTabWidget) ----------------- #
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Corner Add Tab Button
        self.btn_corner_add = QToolButton()
        self.btn_corner_add.setObjectName("AddTabButton")
        self.btn_corner_add.setIcon(IconFactory.create_icon("plus", size=18))
        self.btn_corner_add.setToolTip("New Tab (Click for options, Ctrl+T for Music, Ctrl+Y for Video)")
        self.btn_corner_add.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        add_menu = QMenu(self)
        act_add_music = add_menu.addAction(IconFactory.create_icon("music"), "New YouTube Music Tab (Ctrl+T)")
        act_add_music.triggered.connect(lambda: self.create_new_tab("music", switch_to=True))
        act_add_yt = add_menu.addAction(IconFactory.create_icon("youtube"), "New YouTube Video Tab (Ctrl+Y)")
        act_add_yt.triggered.connect(lambda: self.create_new_tab("youtube", switch_to=True))
        self.btn_corner_add.setMenu(add_menu)
        self.tabs.setCornerWidget(self.btn_corner_add, Qt.Corner.TopRightCorner)

        main_layout.addWidget(self.tabs, 1)

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

    def _setup_shortcuts(self):
        """Registers keyboard shortcuts for browser-style tab management."""
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.create_new_tab("music", switch_to=True))
        QShortcut(QKeySequence("Ctrl+M"), self, lambda: self.create_new_tab("music", switch_to=True))
        QShortcut(QKeySequence("Ctrl+Y"), self, lambda: self.create_new_tab("youtube", switch_to=True))
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_current_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self._next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self._prev_tab)

        for i in range(1, 9):
            QShortcut(QKeySequence(f"Ctrl+{i}"), self, lambda idx=i - 1: self._jump_to_tab(idx))
        QShortcut(QKeySequence("Ctrl+9"), self, self._jump_to_last_tab)

    def _connect_signals(self):
        """Connects Media Controller and Tray signals."""
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

    # ----------------- Dynamic Tab Management ----------------- #

    def create_new_tab(self, service: str = "music", url: str = None, switch_to: bool = True) -> QWebEngineView:
        """
        Creates and loads a new tab for YouTube Music or Standard YouTube.
        """
        if url:
            target_url = url
            is_music = "music.youtube.com" in url.lower()
            service = "music" if is_music else "youtube"
        elif service == "youtube":
            target_url = Config.URL_YOUTUBE
        else:
            target_url = Config.URL_YOUTUBE_MUSIC
            service = "music"

        view = QWebEngineView(self)
        page = YMusicWebPage(self.profile, view, window_ref=self)
        view.setPage(page)
        view.setProperty("service", service)

        # Connect tab signals
        view.titleChanged.connect(lambda title, v=view: self._on_tab_title_changed(v, title))
        view.urlChanged.connect(lambda u, v=view: self._on_tab_url_changed(v, u))

        icon = IconFactory.create_icon("music" if service == "music" else "youtube")
        default_label = "YouTube Music" if service == "music" else "YouTube Video"

        idx = self.tabs.addTab(view, icon, default_label)
        self.tabs.setTabToolTip(idx, default_label)

        if switch_to:
            self.tabs.setCurrentIndex(idx)

        view.setUrl(QUrl(target_url))
        return view

    def create_new_tab_for_page(self) -> QWebEnginePage:
        """Factory method called by YMusicWebPage.createWindow for new tabs."""
        view = self.create_new_tab(service="youtube", switch_to=True)
        return view.page()

    def _on_tab_changed(self, index: int):
        """Handles switching between tabs with auto-pausing on inactive tabs."""
        if index < 0 or not hasattr(self, "tabs"):
            return

        cur_view = self.tabs.widget(index)
        if not isinstance(cur_view, QWebEngineView):
            return

        # Auto-pause audio on all other background tabs if enabled
        if settings.get("auto_pause_inactive_tabs", True):
            pause_js = """
            (function() {
                const video = document.querySelector('video');
                if (video && !video.paused) {
                    video.pause();
                }
            })();
            """
            for i in range(self.tabs.count()):
                if i != index:
                    other_view = self.tabs.widget(i)
                    if isinstance(other_view, QWebEngineView):
                        other_view.page().runJavaScript(pause_js)

        # Update address bar to reflect new active tab
        self.url_bar.setText(cur_view.url().toString())

        # Update window title
        t = cur_view.title()
        if t:
            self.setWindowTitle(f"{t} - YMusic")
        else:
            svc = cur_view.property("service") or "music"
            name = "YouTube Music" if svc == "music" else "YouTube Video"
            self.setWindowTitle(f"{name} - YMusic")

        # Immediately update bottom player & tray state
        self.media_ctrl.update_track_info()

    def _on_tab_close_requested(self, index: int):
        """Closes the specified tab, ensuring at least one tab remains open."""
        if self.tabs.count() <= 1:
            # Recreate fresh default tab so app is never blank
            default_svc = settings.get("default_service", "music")
            self.create_new_tab(service=default_svc, switch_to=True)
            self._close_tab_at(0)
        else:
            self._close_tab_at(index)

    def _close_tab_at(self, index: int):
        """Safely stops and cleans up a tab widget."""
        view = self.tabs.widget(index)
        if isinstance(view, QWebEngineView):
            # Clean up audio and page
            view.page().runJavaScript("""
            (function() {
                const video = document.querySelector('video');
                if (video) { video.pause(); video.src = ''; }
            })();
            """)
            view.stop()
            self.tabs.removeTab(index)
            view.setPage(None)
            view.deleteLater()

    def _close_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self._on_tab_close_requested(idx)

    def _next_tab(self):
        count = self.tabs.count()
        if count > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % count)

    def _prev_tab(self):
        count = self.tabs.count()
        if count > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % count)

    def _jump_to_tab(self, idx: int):
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)

    def _jump_to_last_tab(self):
        if self.tabs.count() > 0:
            self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def _on_tab_title_changed(self, view: QWebEngineView, title: str):
        """Dynamically truncates and updates tab text and tooltip."""
        idx = self.tabs.indexOf(view)
        if idx >= 0 and title:
            clean_title = (
                title.replace(" - YouTube Music", "")
                .replace(" - YouTube", "")
                .strip()
            )
            short_title = clean_title[:24] + ("..." if len(clean_title) > 24 else "")
            self.tabs.setTabText(idx, short_title or "Tab")
            self.tabs.setTabToolTip(idx, f"{title}\n{view.url().toString()}")

            if self._get_current_view() == view:
                self.setWindowTitle(f"{title} - YMusic")

    def _on_tab_url_changed(self, view: QWebEngineView, url: QUrl):
        """Updates URL bar and service icon when URL changes."""
        if self._get_current_view() == view:
            self.url_bar.setText(url.toString())

        idx = self.tabs.indexOf(view)
        if idx >= 0:
            url_str = url.toString().lower()
            is_music = "music.youtube.com" in url_str
            self.tabs.setTabIcon(idx, IconFactory.create_icon("music" if is_music else "youtube"))

    # ----------------- Navigation Actions ----------------- #

    def _go_back(self):
        """Navigates back in the current web view history."""
        view = self._get_current_view()
        if view:
            view.back()

    def _go_forward(self):
        """Navigates forward in the current web view history."""
        view = self._get_current_view()
        if view:
            view.forward()

    def _reload_page(self):
        """Reloads the current web view page."""
        view = self._get_current_view()
        if view:
            view.reload()

    def _on_search_or_navigate(self):
        """Handles navigation or search from the URL bar."""
        text = self.url_bar.text().strip()
        if not text:
            return

        view = self._get_current_view()
        if not view:
            view = self.create_new_tab("music", switch_to=True)

        if text.startswith("http://") or text.startswith("https://"):
            target_url = text
        elif "." in text and " " not in text:
            target_url = f"https://{text}"
        else:
            svc = view.property("service") or "music"
            import urllib.parse
            query = urllib.parse.quote_plus(text)
            if svc == "youtube":
                target_url = f"https://www.youtube.com/results?search_query={query}"
            else:
                target_url = f"https://music.youtube.com/search?q={query}"

        view.setUrl(QUrl(target_url))

    def switch_to_music(self):
        """Creates or switches to YouTube Music tab."""
        self.create_new_tab("music", switch_to=True)

    def switch_to_youtube(self):
        """Creates or switches to Standard YouTube tab."""
        self.create_new_tab("youtube", switch_to=True)

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
            cur = self._get_current_view()
            is_music = cur and "music.youtube.com" in cur.url().toString().lower()
            active_name = "YouTube Music" if is_music else "YouTube Video"
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
