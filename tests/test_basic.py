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


if __name__ == "__main__":
    unittest.main()
