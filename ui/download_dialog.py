"""
Download Dialog and Download Manager UI for YMusic Desktop.
Provides:
1. QuickDownloadDialog: Streamlined modal for setting format/quality & initiating downloads.
2. DownloadManagerWindow: Dedicated download manager displaying active progress, speeds, and history.
"""

import os
import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QFileDialog,
    QProgressBar,
    QScrollArea,
    QWidget,
    QFrame,
    QMessageBox,
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from core.downloader import download_manager, DownloadTask
from ui.icons import IconFactory
from config import settings


class QuickDownloadDialog(QDialog):
    """
    Dialog for configuring and starting a download for the currently playing URL.
    """

    download_started = pyqtSignal(str)

    def __init__(self, current_url: str, default_title: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Media - YMusic")
        self.resize(520, 420)
        self.url = current_url
        self.default_title = default_title

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Title
        title_lbl = QLabel("⬇️ Download Audio / Video")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_lbl)

        # URL / Track details
        url_box = QVBoxLayout()
        url_lbl = QLabel(f"<b>Target:</b> {self.default_title or self.url}")
        url_lbl.setWordWrap(True)
        url_lbl.setStyleSheet("color: #cccccc; font-size: 12px;")
        url_box.addWidget(url_lbl)
        layout.addLayout(url_box)

        # Download Type Selector
        type_layout = QHBoxLayout()
        type_lbl = QLabel("Download Type:")
        type_lbl.setFixedWidth(120)
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Audio Only (Recommended)", "Full Video (MP4)"])
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(type_lbl)
        type_layout.addWidget(self.combo_type)
        layout.addLayout(type_layout)

        # Format & Quality Preset
        format_layout = QHBoxLayout()
        format_lbl = QLabel("Format / Quality:")
        format_lbl.setFixedWidth(120)
        self.combo_format = QComboBox()
        self._populate_audio_formats()
        format_layout.addWidget(format_lbl)
        format_layout.addWidget(self.combo_format)
        layout.addLayout(format_layout)

        # Download Directory Selector
        dir_layout = QHBoxLayout()
        dir_lbl = QLabel("Save Folder:")
        dir_lbl.setFixedWidth(120)
        self.txt_dir = QLineEdit(settings.get("download_dir"))
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setFixedWidth(85)
        self.btn_browse.clicked.connect(self._browse_directory)
        dir_layout.addWidget(dir_lbl)
        dir_layout.addWidget(self.txt_dir)
        dir_layout.addWidget(self.btn_browse)
        layout.addLayout(dir_layout)

        # Options Checkboxes
        opts_layout = QVBoxLayout()
        self.chk_metadata = QCheckBox("Embed Track ID3 Metadata (Artist, Title, Album)")
        self.chk_metadata.setChecked(settings.get("embed_metadata", True))
        self.chk_thumbnail = QCheckBox("Embed High-Resolution Album Art Thumbnail")
        self.chk_thumbnail.setChecked(settings.get("embed_thumbnail", True))
        opts_layout.addWidget(self.chk_metadata)
        opts_layout.addWidget(self.chk_thumbnail)
        layout.addLayout(opts_layout)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_download = QPushButton("Start Download")
        self.btn_download.setProperty("class", "primary")
        self.btn_download.setStyleSheet(
            "background-color: #ff0033; color: #ffffff; font-weight: bold; padding: 9px 24px; border-radius: 6px;"
        )
        self.btn_download.clicked.connect(self._start_download)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_download)
        layout.addLayout(btn_layout)

    def _populate_audio_formats(self):
        self.combo_format.clear()
        self.combo_format.addItem("MP3 - 320 kbps (High Quality)", ("audio", "mp3", "320"))
        self.combo_format.addItem("MP3 - 256 kbps (Standard)", ("audio", "mp3", "256"))
        self.combo_format.addItem("MP3 - 192 kbps (Compact)", ("audio", "mp3", "192"))
        self.combo_format.addItem("Opus - Best Quality (Native YouTube Audio)", ("audio", "opus", "best"))
        self.combo_format.addItem("M4A / AAC - Best Quality (Apple Friendly)", ("audio", "m4a", "best"))
        self.combo_format.addItem("FLAC - Lossless Audio", ("audio", "flac", "best"))

    def _populate_video_formats(self):
        self.combo_format.clear()
        self.combo_format.addItem("MP4 - Best Available Resolution (Up to 4K)", ("video", "best", "best"))
        self.combo_format.addItem("MP4 - 1080p Full HD", ("video", "1080p", "1080p"))
        self.combo_format.addItem("MP4 - 720p HD", ("video", "720p", "720p"))
        self.combo_format.addItem("MP4 - 480p Standard", ("video", "480p", "480p"))

    def _on_type_changed(self, index: int):
        if index == 0:
            self._populate_audio_formats()
            self.chk_thumbnail.setEnabled(True)
        else:
            self._populate_video_formats()

    def _browse_directory(self):
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", self.txt_dir.text()
        )
        if chosen:
            self.txt_dir.setText(chosen)
            settings.set("download_dir", chosen)

    def _start_download(self):
        if not self.url or not self.url.startswith("http"):
            QMessageBox.warning(self, "Invalid URL", "No valid YouTube URL detected.")
            return

        save_dir = self.txt_dir.text().strip()
        if save_dir:
            try:
                Path(save_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot create directory: {e}")
                return

        # Read format configuration
        data = self.combo_format.currentData()
        dl_type, format_name, quality = data

        # Persist settings
        settings.set("download_dir", save_dir)
        settings.set("embed_metadata", self.chk_metadata.isChecked())
        settings.set("embed_thumbnail", self.chk_thumbnail.isChecked())

        task = download_manager.start_download(
            url=self.url,
            download_type=dl_type,
            format_name=format_name,
            quality=quality,
            output_dir=save_dir,
            embed_metadata=self.chk_metadata.isChecked(),
            embed_thumbnail=self.chk_thumbnail.isChecked(),
        )

        self.download_started.emit(task.task_id)
        self.accept()


class DownloadItemWidget(QFrame):
    """Widget row representing a single active or completed download."""

    def __init__(self, task: DownloadTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.setObjectName("DownloadItem")
        self.setStyleSheet("""
            #DownloadItem {
                background-color: #1a1a1a;
                border: 1px solid #292929;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Top row: Title and format badge
        top_row = QHBoxLayout()
        self.lbl_title = QLabel(self.task.title or self.task.url)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px;")
        self.lbl_title.setWordWrap(True)

        self.lbl_badge = QLabel(f"[{self.task.format_name.upper()}]")
        self.lbl_badge.setStyleSheet("color: #ff0033; font-weight: bold; font-size: 11px;")

        top_row.addWidget(self.lbl_title, 1)
        top_row.addWidget(self.lbl_badge, 0)
        layout.addLayout(top_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(self.task.progress_percent))
        layout.addWidget(self.progress_bar)

        # Bottom row: Speed, ETA, Status & Action buttons
        bottom_row = QHBoxLayout()
        self.lbl_status = QLabel(f"Status: {self.task.status.capitalize()}")
        self.lbl_status.setStyleSheet("color: #888888; font-size: 11px;")

        self.lbl_metrics = QLabel(f"{self.task.downloaded_bytes_str} / {self.task.total_bytes_str} • {self.task.speed_str} • ETA: {self.task.eta_str}")
        self.lbl_metrics.setStyleSheet("color: #aaaaaa; font-size: 11px;")

        self.btn_open_file = QPushButton("Open File")
        self.btn_open_file.setVisible(False)
        self.btn_open_file.clicked.connect(self._open_file)

        self.btn_open_folder = QPushButton("Folder")
        self.btn_open_folder.setVisible(False)
        self.btn_open_folder.clicked.connect(self._open_folder)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._cancel_task)

        bottom_row.addWidget(self.lbl_status)
        bottom_row.addWidget(self.lbl_metrics)
        bottom_row.addStretch()
        bottom_row.addWidget(self.btn_open_file)
        bottom_row.addWidget(self.btn_open_folder)
        bottom_row.addWidget(self.btn_cancel)
        layout.addLayout(bottom_row)

    def update_progress(self, percent: float, speed: str, eta: str, downloaded: str, total: str, status: str):
        self.progress_bar.setValue(int(percent))
        self.lbl_status.setText(f"Status: {status.capitalize()}")
        self.lbl_metrics.setText(f"{downloaded} / {total} • {speed} • ETA: {eta}")
        if self.task.title:
            self.lbl_title.setText(self.task.title)

    def set_completed(self, filepath: str, success: bool, err_msg: str):
        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText("Status: Completed ✓")
            self.lbl_status.setStyleSheet("color: #2ba640; font-weight: bold; font-size: 11px;")
            self.lbl_metrics.setText(os.path.basename(filepath))
            self.btn_cancel.setVisible(False)
            self.btn_open_file.setVisible(True)
            self.btn_open_folder.setVisible(True)
            if self.task.title:
                self.lbl_title.setText(self.task.title)
        else:
            self.lbl_status.setText(f"Status: Failed ✕ ({err_msg[:40]})")
            self.lbl_status.setStyleSheet("color: #ff3333; font-weight: bold; font-size: 11px;")
            self.btn_cancel.setText("Dismiss")
            self.btn_cancel.clicked.connect(self.deleteLater)

    def _cancel_task(self):
        download_manager.cancel_task(self.task.task_id)
        self.lbl_status.setText("Status: Cancelled")
        self.btn_cancel.setEnabled(False)

    def _open_file(self):
        if self.task.final_filepath and os.path.exists(self.task.final_filepath):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.task.final_filepath))

    def _open_folder(self):
        folder = self.task.output_dir
        if self.task.final_filepath and os.path.exists(self.task.final_filepath):
            folder = os.path.dirname(self.task.final_filepath)
        if folder:
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


class DownloadManagerWindow(QDialog):
    """
    Dedicated window / dialog for inspecting all active and completed downloads.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager - YMusic")
        self.resize(650, 480)

        self.item_widgets = {}

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        top_bar = QHBoxLayout()
        lbl_head = QLabel("📥 Download Manager")
        lbl_head.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        
        btn_open_dest = QPushButton("Open Downloads Folder")
        btn_open_dest.clicked.connect(self._open_default_folder)

        btn_clear = QPushButton("Clear Completed")
        btn_clear.clicked.connect(self._clear_completed)

        top_bar.addWidget(lbl_head)
        top_bar.addStretch()
        top_bar.addWidget(btn_open_dest)
        top_bar.addWidget(btn_clear)
        layout.addLayout(top_bar)

        # Scroll Area for Task Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        # Load any existing tasks
        for task in download_manager.tasks.values():
            self._add_task_widget(task)

    def _connect_signals(self):
        download_manager.task_added.connect(self._add_task_widget)
        download_manager.task_progress.connect(self._update_task_progress)
        download_manager.task_completed.connect(self._on_task_completed)

    def _add_task_widget(self, task: DownloadTask):
        if task.task_id not in self.item_widgets:
            widget = DownloadItemWidget(task, self)
            self.item_widgets[task.task_id] = widget
            self.scroll_layout.addWidget(widget)

    def _update_task_progress(self, task_id, percent, speed, eta, downloaded, total, status):
        widget = self.item_widgets.get(task_id)
        if widget:
            widget.update_progress(percent, speed, eta, downloaded, total, status)

    def _on_task_completed(self, task_id, filepath, success, err_msg):
        widget = self.item_widgets.get(task_id)
        if widget:
            widget.set_completed(filepath, success, err_msg)

    def _open_default_folder(self):
        dest = settings.get("download_dir")
        if dest:
            try:
                Path(dest).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            QDesktopServices.openUrl(QUrl.fromLocalFile(dest))

    def _clear_completed(self):
        for task_id, widget in list(self.item_widgets.items()):
            if widget.task.status in ("finished", "error", "cancelled"):
                self.scroll_layout.removeWidget(widget)
                widget.deleteLater()
                del self.item_widgets[task_id]
