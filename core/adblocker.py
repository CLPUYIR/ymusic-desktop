"""
Ad Blocker Engine for YMusic Desktop.
Implements:
1. QWebEngineUrlRequestInterceptor for blocking external ad network domains & trackers.
2. Injected CSS (TrustedHTML compliant) for hiding banners, sponsored units, and upsell popups.
3. Injected JavaScript for accurate in-stream video ad detection, auto-skipping, and playback speed restoration.
"""

from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
    QWebEngineScript,
)
from PyQt6.QtCore import QUrl


class AdBlockUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Intercepts network requests across the web view and blocks external ad networks,
    trackers, and metrics domains without breaking internal YouTube player media streams.
    """

    BLOCKED_DOMAINS = {
        "doubleclick.net",
        "googleads.g.doubleclick.net",
        "pubads.g.doubleclick.net",
        "securepubads.g.doubleclick.net",
        "pagead2.googlesyndication.com",
        "adservice.google.com",
        "google-analytics.com",
        "analytics.google.com",
        "stats.g.doubleclick.net",
        "cm.g.doubleclick.net",
        "fls-na.amazon-adsystem.com",
        "ad.doubleclick.net",
        "static.doubleclick.net",
        "googlesyndication.com",
    }

    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled
        self.blocked_count = 0

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        """
        Blocks external ad domain requests.
        """
        if not self.enabled:
            return

        url: QUrl = info.requestUrl()
        host = url.host().lower()

        # Check if host matches or ends with any blocked domain
        for blocked_host in self.BLOCKED_DOMAINS:
            if host == blocked_host or host.endswith("." + blocked_host):
                info.block(True)
                self.blocked_count += 1
                return


# CSS to cleanly remove promotional banners and overlay ads without breaking page layout
ADBLOCK_CSS = """
/* Hide promotional banners and overlay ad items */
.ytp-ad-overlay-container,
.ytp-ad-overlay-slot,
.ytp-ad-text-overlay,
.ytp-ad-image-overlay,
ytd-promoted-sparkles-web-renderer,
ytd-promoted-sparkles-text-search-web-renderer,
ytd-promoted-video-renderer,
ytd-display-ad-renderer,
ytd-banner-promo-renderer,
ytd-in-feed-ad-layout-renderer,
ytd-ad-slot-renderer,
#player-ads,
#masthead-ad,
ytmusic-mealbar-promo-renderer,
ytmusic-banner-promo-renderer,
ytmusic-popup-container ytmusic-upsell-dialog-renderer,
tp-yt-paper-dialog:has(ytmusic-upsell-dialog-renderer) {
    display: none !important;
    visibility: hidden !important;
    height: 0px !important;
    width: 0px !important;
    pointer-events: none !important;
    opacity: 0 !important;
}
"""

# JavaScript for precision video ad skipping and auto-dismissing popups
ADBLOCK_JS = """
(function() {
    'use strict';

    let wasAdShowing = false;

    function handleVideoAds() {
        // Precise YouTube ad player check
        const player = document.querySelector('#movie_player, .html5-video-player');
        const isAdShowing = player && (player.classList.contains('ad-showing') || player.classList.contains('ad-interrupting'));
        const video = document.querySelector('video');

        if (isAdShowing && video) {
            wasAdShowing = true;
            
            // 1. Immediately click any skip buttons if available
            const skipButtons = document.querySelectorAll(
                '.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytp-skip-ad-button, .ytp-ad-skip-button-text, button.ytp-ad-skip-button-modern, .ytp-ad-preview-container button'
            );
            for (const btn of skipButtons) {
                if (btn && typeof btn.click === 'function') {
                    btn.click();
                }
            }

            // 2. Fast forward the in-stream ad video safely
            try {
                video.muted = true;
                video.playbackRate = 16.0;
                if (isFinite(video.duration) && video.duration > 0 && video.currentTime < video.duration - 0.2) {
                    video.currentTime = video.duration - 0.1;
                }
            } catch (e) {}
        } else if (wasAdShowing && video) {
            // Ad has finished! Restore normal playback speed and unmute
            wasAdShowing = false;
            try {
                if (video.playbackRate > 2.0) {
                    video.playbackRate = 1.0;
                }
                video.muted = false;
            } catch (e) {}
        }

        // Close overlay close buttons
        const overlayCloseButtons = document.querySelectorAll(
            '.ytp-ad-overlay-close-button, .ytp-ad-overlay-close-container'
        );
        for (const closeBtn of overlayCloseButtons) {
            if (closeBtn && typeof closeBtn.click === 'function') {
                closeBtn.click();
            }
        }

        // Auto-dismiss "Still watching?" dialog
        const dismissBtns = document.querySelectorAll(
            'yt-button-renderer#dismiss-button, ytmusic-upsell-dialog-renderer #dismiss-button'
        );
        for (const dBtn of dismissBtns) {
            if (dBtn && typeof dBtn.click === 'function') {
                dBtn.click();
            }
        }
    }

    // Run periodic ad monitor
    setInterval(handleVideoAds, 250);

    const observer = new MutationObserver(() => {
        handleVideoAds();
    });

    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            if (document.body) {
                observer.observe(document.body, { childList: true, subtree: true });
            }
        });
    }
})();
"""


def create_adblock_script() -> QWebEngineScript:
    """
    Creates a persistent QWebEngineScript for DOM-level ad elimination and hiding.
    Uses textContent to comply with YouTube's TrustedHTML CSP.
    """
    script = QWebEngineScript()
    script.setName("YMusicAdBlockScript")
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(True)

    # Use textContent to avoid TrustedHTML violation
    full_source = f"""
    (function() {{
        try {{
            const style = document.createElement('style');
            style.type = 'text/css';
            style.textContent = `{ADBLOCK_CSS}`;
            if (document.head) {{
                document.head.appendChild(style);
            }} else if (document.documentElement) {{
                document.documentElement.appendChild(style);
            }}
        }} catch(e) {{}}
    }})();
    {ADBLOCK_JS}
    """
    script.setSourceCode(full_source)
    return script
