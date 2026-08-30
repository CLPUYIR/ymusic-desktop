"""
Basic Unit Tests for YMusic Desktop modules.
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_imports():
    import config
    from core import adblocker, downloader, media_controller, web_page
    from ui import icons, styles, download_dialog, main_window
    assert config.Config.APP_NAME == "YMusic Desktop"
