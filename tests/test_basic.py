"""
Basic Unit Tests for YMusic Desktop modules.
"""
import sys
import os
import unittest

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestYMusicDesktop(unittest.TestCase):
    def test_imports_and_config(self):
        import config
        from core import adblocker, downloader, media_controller, web_page
        from ui import icons, styles, download_dialog, main_window
        self.assertEqual(config.Config.APP_NAME, "YMusic Desktop")
        self.assertIn("auto_pause_inactive_tabs", config.settings.defaults)
        self.assertTrue(config.settings.get("auto_pause_inactive_tabs"))

    def test_icons_and_tabs(self):
        from PyQt6.QtWidgets import QApplication
        from ui.icons import IconFactory
        app = QApplication.instance() or QApplication(sys.argv)
        
        icon_music = IconFactory.create_icon("music")
        icon_yt = IconFactory.create_icon("youtube")
        icon_plus = IconFactory.create_icon("plus")
        icon_add = IconFactory.create_icon("add")
        
        self.assertFalse(icon_music.isNull())
        self.assertFalse(icon_yt.isNull())
        self.assertFalse(icon_plus.isNull())
        self.assertFalse(icon_add.isNull())

    def test_adblocker_domains(self):
        from core.adblocker import AdBlockUrlRequestInterceptor
        from PyQt6.QtCore import QUrl

        interceptor = AdBlockUrlRequestInterceptor(enabled=True)

        blocked_urls = [
            "https://doubleclick.net/ad",
            "https://googleads.g.doubleclick.net/pagead/id",
            "https://ad.youtube.com/track",
            "https://ads.youtube.com/serve",
            "https://video-stats.l.google.com/stats",
            "https://s0.2mdn.net/ads/ad.js",
            "https://static.doubleclick.net/instream/ad_status.js",
            "https://www.googleadservices.com/pagead/conversion/",
            "https://googleadservices.com/pagead/conversion/",
            "https://ade.googlesyndication.com/pagead",
            "https://adservice.google.de/adsid/google/ui",
            "https://adservice.google.co.uk/adsid/google/ui",
            "https://www.youtube.com/api/stats/ads?v=123",
            "https://www.youtube.com/pagead/viewthroughconversion/123",
        ]

        allowed_urls = [
            "https://music.youtube.com/",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://rr1---sn-4g5edn6e.googlevideo.com/videoplayback?expire=123",
            "https://accounts.google.com/signin",
        ]

        for url in blocked_urls:
            self.assertTrue(interceptor.is_blocked(QUrl(url)), f"Expected {url} to be blocked")

        for url in allowed_urls:
            self.assertFalse(interceptor.is_blocked(QUrl(url)), f"Expected {url} to NOT be blocked")


if __name__ == "__main__":
    unittest.main()
