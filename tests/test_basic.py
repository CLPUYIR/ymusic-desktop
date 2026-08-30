"""
Basic Unit Tests for YMusic Desktop modules.
"""

def test_imports():
    import config
    from core import adblocker, downloader, media_controller, web_page
    from ui import icons, styles, download_dialog, main_window
    assert config.Config.APP_NAME == "YMusic Desktop"
