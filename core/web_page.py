"""
Custom QWebEnginePage and Web Profile setup for YMusic Desktop.
Provides:
1. Background playback persistence (spoofing Page Visibility API so media plays when minimized/hidden).
2. Desktop User-Agent handling and permission grants.
3. Link handling and navigation policy.
"""

from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineScript,
)
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from config import settings


# JavaScript injected at DocumentCreation to prevent YouTube from pausing when window is minimized
BACKGROUND_PLAYBACK_JS = """
(function() {
    'use strict';
    
    // Override Document Visibility API to always report as visible
    try {
        Object.defineProperty(document, 'hidden', {
            get: function() { return false; },
            configurable: true
        });
        Object.defineProperty(document, 'visibilityState', {
            get: function() { return 'visible'; },
            configurable: true
        });
        Object.defineProperty(document, 'webkitHidden', {
            get: function() { return false; },
            configurable: true
        });
        Object.defineProperty(document, 'webkitVisibilityState', {
            get: function() { return 'visible'; },
            configurable: true
        });

        // Intercept visibility change events
        window.addEventListener('visibilitychange', function(e) {
            if (document.visibilityState === 'hidden') {
                e.stopImmediatePropagation();
            }
        }, true);
    } catch (e) {}
})();
"""


class YMusicWebPage(QWebEnginePage):
    """
    Custom WebEnginePage with enhanced playback persistence,
    custom permission handler, and window creation rules.
    """

    status_message_requested = pyqtSignal(str)

    def __init__(self, profile: QWebEngineProfile, parent=None, window_ref=None):
        super().__init__(profile, parent)
        self.window_ref = window_ref
        self.featurePermissionRequested.connect(self._handle_permission_request)
        self.apply_page_settings()
        self._inject_background_script()

    def apply_page_settings(self):
        """Configures WebEngine settings for optimal media playback and smoothness."""
        page_settings = self.settings()
        
        # Audio / Media autoplay and persistence
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.WebGLEnabled, True
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.PluginsEnabled, True
        )

    def _inject_background_script(self):
        """Injects background playback persistence script at DocumentCreation."""
        script = QWebEngineScript()
        script.setName("YMusicBackgroundPlaybackScript")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)  # Only run on main frame
        script.setSourceCode(BACKGROUND_PLAYBACK_JS)
        self.profile().scripts().insert(script)

    def _handle_permission_request(self, security_origin: QUrl, feature: QWebEnginePage.Feature):
        """Grants necessary permissions for notifications and audio."""
        if feature in (
            QWebEnginePage.Feature.Notifications,
            QWebEnginePage.Feature.MediaAudioCapture,
        ):
            self.setFeaturePermission(
                security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )
        else:
            self.setFeaturePermission(
                security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
            )

    def acceptNavigationRequest(self, url: QUrl, _type: QWebEnginePage.NavigationType, isMainFrame: bool) -> bool:
        """
        Opens external non-Google/YouTube links in the system default browser.
        """
        host = url.host().lower()

        allowed_domains = [
            "youtube.com",
            "music.youtube.com",
            "accounts.google.com",
            "google.com",
            "gstatic.com",
            "googleusercontent.com",
        ]

        is_allowed = any(host == d or host.endswith("." + d) for d in allowed_domains)

        if not is_allowed and isMainFrame and _type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False

        return super().acceptNavigationRequest(url, _type, isMainFrame)

    def createWindow(self, _type: QWebEnginePage.WebWindowType) -> QWebEnginePage:
        if self.window_ref and hasattr(self.window_ref, "create_new_tab_for_page"):
            new_page = self.window_ref.create_new_tab_for_page()
            if new_page:
                return new_page
        return self
