"""
Media Controller Bridge for YMusic Desktop.
Executes JavaScript inside the YouTube / YouTube Music WebEngine context to
control playback, seek, adjust volume, and extract current track metadata.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWebEngineCore import QWebEnginePage
from typing import Optional, Dict, Any, Callable


class MediaController(QObject):
    """
    Controls media playback and listens for state changes
    (track changes, play/pause status, duration/progress).
    """

    # Signals
    track_changed = pyqtSignal(dict)  # Emits metadata dict when song/video changes
    playback_state_changed = pyqtSignal(bool)  # is_playing
    volume_changed = pyqtSignal(int)  # 0 to 100

    def __init__(self, page_getter: Callable[[], Optional[QWebEnginePage]], parent=None):
        super().__init__(parent)
        self._get_page = page_getter
        self.current_track: Dict[str, Any] = {
            "title": "No media playing",
            "artist": "",
            "album": "",
            "duration": "0:00",
            "current_time": "0:00",
            "is_playing": False,
            "thumbnail_url": "",
            "url": "",
        }
        self._last_title = ""
        self._last_state = False

        # Polling timer for metadata updates
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1000)  # Check every second
        self._poll_timer.timeout.connect(self.update_track_info)
        self._poll_timer.start()

    @property
    def page(self) -> Optional[QWebEnginePage]:
        return self._get_page()

    def run_js(self, script: str, callback: Optional[Callable[[Any], None]] = None):
        """Safely executes JavaScript in the current page context."""
        p = self.page
        if p is not None:
            if callback:
                p.runJavaScript(script, callback)
            else:
                p.runJavaScript(script)

    # ------------------ Playback Controls ------------------ #

    def play_pause(self):
        """Toggles play / pause state."""
        script = """
        (function() {
            // Check YouTube Music player button
            const ytmPlayBtn = document.querySelector('ytmusic-player-bar #play-pause-button');
            if (ytmPlayBtn) {
                ytmPlayBtn.click();
                return;
            }
            // Check Standard YouTube player button
            const ytPlayBtn = document.querySelector('.ytp-play-button');
            if (ytPlayBtn) {
                ytPlayBtn.click();
                return;
            }
            // Fallback: direct HTML5 video element control
            const video = document.querySelector('video');
            if (video) {
                if (video.paused) { video.play(); } else { video.pause(); }
            }
        })();
        """
        self.run_js(script)
        # Immediate update
        QTimer.singleShot(250, self.update_track_info)

    def next_track(self):
        """Skips to the next track/video."""
        script = """
        (function() {
            // YouTube Music next button
            const ytmNext = document.querySelector('ytmusic-player-bar .next-button');
            if (ytmNext) {
                ytmNext.click();
                return;
            }
            // Standard YouTube next button
            const ytNext = document.querySelector('.ytp-next-button');
            if (ytNext) {
                ytNext.click();
                return;
            }
        })();
        """
        self.run_js(script)
        QTimer.singleShot(600, self.update_track_info)

    def previous_track(self):
        """Returns to the previous track or restarts current track."""
        script = """
        (function() {
            // YouTube Music previous button
            const ytmPrev = document.querySelector('ytmusic-player-bar .previous-button');
            if (ytmPrev) {
                ytmPrev.click();
                return;
            }
            // Standard YouTube seek to start or history
            const video = document.querySelector('video');
            if (video) {
                video.currentTime = 0;
            }
        })();
        """
        self.run_js(script)
        QTimer.singleShot(600, self.update_track_info)

    def seek_forward(self, seconds: int = 10):
        """Seeks forward by specified seconds."""
        script = f"""
        (function() {{
            const video = document.querySelector('video');
            if (video) {{
                video.currentTime = Math.min(video.duration || 0, video.currentTime + {seconds});
            }}
        }})();
        """
        self.run_js(script)

    def seek_backward(self, seconds: int = 10):
        """Seeks backward by specified seconds."""
        script = f"""
        (function() {{
            const video = document.querySelector('video');
            if (video) {{
                video.currentTime = Math.max(0, video.currentTime - {seconds});
            }}
        }})();
        """
        self.run_js(script)

    def set_volume(self, percent: int):
        """Sets playback volume (0 to 100)."""
        vol = max(0, min(100, percent)) / 100.0
        script = f"""
        (function() {{
            const video = document.querySelector('video');
            if (video) {{
                video.volume = {vol};
                video.muted = false;
            }}
        }})();
        """
        self.run_js(script)
        self.volume_changed.emit(percent)

    def toggle_mute(self):
        """Toggles audio mute."""
        script = """
        (function() {
            const video = document.querySelector('video');
            if (video) {
                video.muted = !video.muted;
            }
        })();
        """
        self.run_js(script)

    def like_track(self):
        """Likes the currently playing track."""
        script = """
        (function() {
            const likeBtn = document.querySelector('ytmusic-like-button-renderer #button-shape-like button, #top-level-buttons-computed ytd-toggle-button-renderer:first-child button');
            if (likeBtn) {
                likeBtn.click();
            }
        })();
        """
        self.run_js(script)

    # ------------------ Metadata Extraction ------------------ #

    def update_track_info(self):
        """Queries the DOM for current track metadata."""
        script = """
        (function() {
            let data = {
                title: '',
                artist: '',
                album: '',
                duration: '0:00',
                current_time: '0:00',
                is_playing: false,
                thumbnail_url: '',
                url: window.location.href
            };

            const video = document.querySelector('video');
            if (video) {
                data.is_playing = !video.paused && !video.ended && video.readyState > 2;
                
                // Format helper
                const formatTime = (secs) => {
                    if (isNaN(secs)) return '0:00';
                    const m = Math.floor(secs / 60);
                    const s = Math.floor(secs % 60);
                    return m + ':' + (s < 10 ? '0' : '') + s;
                };
                data.current_time = formatTime(video.currentTime);
                data.duration = formatTime(video.duration);
            }

            // Check YouTube Music player bar
            const ytmTitle = document.querySelector('ytmusic-player-bar .title');
            const ytmByline = document.querySelector('ytmusic-player-bar .byline');
            const ytmThumb = document.querySelector('ytmusic-player-bar .image');

            if (ytmTitle && ytmTitle.textContent.trim()) {
                data.title = ytmTitle.textContent.trim();
                if (ytmByline) {
                    // Extract artist and album from byline links or text
                    const links = ytmByline.querySelectorAll('a');
                    if (links.length >= 1) {
                        data.artist = links[0].textContent.trim();
                    }
                    if (links.length >= 2) {
                        data.album = links[1].textContent.trim();
                    } else if (!data.artist) {
                        data.artist = ytmByline.textContent.trim();
                    }
                }
                if (ytmThumb) {
                    data.thumbnail_url = ytmThumb.src || '';
                }
            } else {
                // Check Standard YouTube metadata
                const ytTitle = document.querySelector('h1.ytd-watch-metadata yt-formatted-string, #title h1 yt-formatted-string');
                const ytChannel = document.querySelector('#owner #channel-name a, ytd-channel-name a');
                
                if (ytTitle && ytTitle.textContent.trim()) {
                    data.title = ytTitle.textContent.trim();
                } else if (document.title && !document.title.includes('YouTube Music')) {
                    data.title = document.title.replace(' - YouTube', '').trim();
                }
                if (ytChannel) {
                    data.artist = ytChannel.textContent.trim();
                }
            }

            // Fallback for mediaSession API
            if (navigator.mediaSession && navigator.mediaSession.metadata) {
                const meta = navigator.mediaSession.metadata;
                if (!data.title && meta.title) data.title = meta.title;
                if (!data.artist && meta.artist) data.artist = meta.artist;
                if (!data.album && meta.album) data.album = meta.album;
                if (!data.thumbnail_url && meta.artwork && meta.artwork.length > 0) {
                    data.thumbnail_url = meta.artwork[meta.artwork.length - 1].src;
                }
            }

            return data;
        })();
        """
        self.run_js(script, self._on_metadata_received)

    def _on_metadata_received(self, result: Optional[Dict[str, Any]]):
        if not result or not isinstance(result, dict):
            return

        title = result.get("title", "").strip()
        is_playing = result.get("is_playing", False)

        self.current_track = result

        # Check if playback state changed
        if is_playing != self._last_state:
            self._last_state = is_playing
            self.playback_state_changed.emit(is_playing)

        # Check if song/title changed
        if title and title != self._last_title:
            self._last_title = title
            self.track_changed.emit(result)
