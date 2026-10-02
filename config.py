"""
Configuration and Settings Manager for YMusic Desktop.
Handles persistent storage of user preferences, download directories,
ad-blocking filters, and audio/video format options.
"""

import json
import os
from pathlib import Path
from PyQt6.QtCore import QStandardPaths


class Config:
    APP_NAME = "YMusic Desktop"
    APP_ORG = "YMusicProject"
    APP_VERSION = "1.0.0"

    # Default URLs
    URL_YOUTUBE_MUSIC = "https://music.youtube.com"
    URL_YOUTUBE = "https://www.youtube.com"

    # User-Agent string to ensure desktop UI without unwanted browser warnings
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self):
        # Base config directory in user app data
        base_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation
        )
        if not base_dir:
            self.config_dir = Path.home() / ".ymusic_desktop"
        else:
            p = Path(base_dir)
            if self.APP_NAME.lower() not in p.as_posix().lower():
                self.config_dir = p / self.APP_NAME
            else:
                self.config_dir = p
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "settings.json"

        # Default music download location
        default_music_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.MusicLocation
        )
        if not default_music_dir:
            default_music_dir = str(Path.home() / "Music")
        
        # Ensure default download directory exists
        try:
            Path(default_music_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self.defaults = {
            "default_service": "music",  # 'music' or 'youtube'
            "auto_pause_inactive_tabs": True,  # Auto-pause audio on background tabs
            "adblock_enabled": True,
            "element_hiding_enabled": True,
            "minimize_to_tray": True,
            "close_to_tray": True,
            "start_minimized": False,
            "audio_format": "mp3",  # 'mp3', 'opus', 'm4a', 'flac'
            "audio_quality": "320",  # '320', '256', '192', '128'
            "video_quality": "best",  # 'best', '1080p', '720p', '480p'
            "download_dir": default_music_dir,
            "embed_metadata": True,
            "embed_thumbnail": True,
            "volume": 100,
            "notifications_enabled": True,
            "window_geometry": None,
        }

        self.data = self.defaults.copy()
        self.load()

    def load(self):
        """Loads configuration from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"[Config] Error loading settings: {e}")

    def save(self):
        """Saves current configuration to JSON file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[Config] Error saving settings: {e}")

    def get(self, key, default=None):
        return self.data.get(key, self.defaults.get(key, default))

    def set(self, key, value):
        self.data[key] = value
        self.save()


# Global config instance
settings = Config()
