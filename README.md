# 🎵 YMusic Desktop

A complete, high-performance, cross-platform desktop client for **YouTube** and **YouTube Music** built using **Python 3**, **PyQt6**, and **QWebEngineView**. Inspired by *YMusic for Android*, this client provides an ad-free, lightweight, and background-playback-enabled desktop experience with built-in media controls and `yt-dlp` stream downloading.

---

## ✨ Features

- **🛡️ Multi-Tier Ad Blocking**:
  - **Network Interception**: Custom `QWebEngineUrlRequestInterceptor` blocks ad exchanges, tracking domains (`doubleclick.net`, `googleads`, etc.), and YouTube ad delivery endpoints before network requests leave your machine.
  - **DOM Element Hiding**: Injected CSS hides sponsored blocks, promotional banners, and overlay ads.
  - **Video Ad Skipping**: Injected JavaScript `MutationObserver` fast-forwards and auto-skips in-stream video ads instantly.

- **🎧 Background / Minimized Seamless Playback**:
  - Continuous audio streaming without stutters when minimized, occluded, or hidden in the system tray.
  - Chromium power-saver flags configured (`--disable-background-timer-throttling`, `--disable-renderer-backgrounding`).
  - WebEngine visibility spoofing patches `document.hidden` and `document.visibilityState`.

- **🎛️ System Tray & Media Controls**:
  - Minimize-to-tray and close-to-tray support.
  - Tray context menu with dynamic **Play/Pause**, **Next**, **Previous**, and **Download** controls.
  - Real-time track information (Song Title, Artist, Duration) displayed in the tray tooltip and status bar.
  - Desktop notifications when songs change.

- **⬇️ yt-dlp Downloader Integration**:
  - Direct extraction of currently playing video/audio URLs.
  - Background downloads run in a dedicated `QThread` without freezing the UI.
  - **Audio Formats**: MP3 (320kbps / 256kbps / 192kbps), Opus (native YouTube audio), M4A/AAC, FLAC.
  - **Video Formats**: Best MP4 (up to 4K), 1080p Full HD, 720p HD.
  - Automatic **ID3 metadata tagging** (Title, Artist, Album) and **album cover artwork embedding**.
  - Download Manager window with live speed, ETA, progress bars, cancellation, and "Open Containing Folder" actions.

- **🔀 Dual Mode**:
  - One-click toggle between **YouTube Music** (`music.youtube.com`) and **Standard YouTube** (`youtube.com`).

- **🎨 Modern Dark Theme**:
  - Polished interface matching YouTube Music's dark aesthetic with custom vector icons (no external asset files required).

---

## 📁 Project Structure

```
ymusic_desktop/
├── main.py                     # Application entry point & Chromium flags setup
├── config.py                   # Persistent settings & JSON configuration manager
├── requirements.txt            # Python dependencies (PyQt6, PyQt6-WebEngine, yt-dlp)
├── README.md                   # Documentation & setup guide
├── core/
│   ├── __init__.py
│   ├── adblocker.py            # QWebEngineUrlRequestInterceptor & DOM ad skipper
│   ├── web_page.py             # Custom QWebEnginePage & background playback hooks
│   ├── media_controller.py     # JS bridge for YouTube playback control & metadata extraction
│   └── downloader.py           # yt-dlp download worker (QThread) & DownloadManager
└── ui/
    ├── __init__.py
    ├── main_window.py          # Main UI window with toolbar, mini-player & status bar
    ├── tray_icon.py            # System tray icon, notifications & context menu
    ├── download_dialog.py      # Quick download modal & full Download Manager window
    ├── icons.py                # Programmatic vector icon generator (QPainter)
    └── styles.py               # Modern dark theme stylesheets (QSS)
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Python 3.9+**
- **FFmpeg** (Recommended for audio extraction, MP3 conversion, and thumbnail embedding):
  - **Windows**: `winget install Gyan.FFmpeg` or `choco install ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - **Linux (Ubuntu/Debian)**: `sudo apt install ffmpeg`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

#### Optional CLI Arguments:
- Start directly in the system tray:
  ```bash
  python main.py --minimized
  ```
- Start directly on standard YouTube:
  ```bash
  python main.py --service youtube
  ```

---

## 🛠️ Architecture & Key Components

### 1. Ad Blocker (`core/adblocker.py`)
```python
class AdBlockUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString().lower()
        if any(domain in url for domain in BLOCKED_DOMAINS) or any(p.search(url) for p in BLOCKED_PATTERNS):
            info.block(True)
```

### 2. Background Playback Persistence (`core/web_page.py` & `main.py`)
Chromium command line flags applied before `QApplication`:
```python
CHROMIUM_FLAGS = (
    "--disable-background-timer-throttling "
    "--disable-renderer-backgrounding "
    "--disable-backgrounding-occluded-windows "
    "--autoplay-policy=no-user-gesture-required"
)
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = CHROMIUM_FLAGS
```
JavaScript injected at `DocumentCreation`:
```javascript
Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
```

### 3. yt-dlp Background Downloader (`core/downloader.py`)
Runs in a separate `QThread`, emitting real-time signals for download progress, speed, ETA, and status to keep the UI smooth and responsive.

---

## 📜 License
MIT License.
