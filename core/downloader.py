"""
Downloader Module for YMusic Desktop.
Leverages yt-dlp in background QThreads to download:
- High-quality audio (MP3 320k, Opus, M4A, FLAC) with ID3 metadata and embedded cover art.
- Full HD / 4K / 720p video streams with automatic audio muxing.
Automatically detects and bundles FFmpeg via imageio-ffmpeg or system PATH,
with graceful single-stream fallback if FFmpeg is unavailable.
"""

import os
import shutil
import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex, QMutexLocker, QStandardPaths
import yt_dlp


def get_ffmpeg_path() -> Optional[str]:
    """
    Locates FFmpeg executable automatically from imageio-ffmpeg or system PATH.
    """
    # 1. Check bundled imageio_ffmpeg package
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    # 2. Check system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 3. Check typical Windows install locations dynamically
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    system_drive = os.environ.get("SystemDrive", "C:")
    local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    common_paths = [
        os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe", "ffmpeg-*", "bin", "ffmpeg.exe"),
        os.path.join(system_drive + os.sep, "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(program_files, "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for p in common_paths:
        import glob
        matches = glob.glob(p)
        if matches and os.path.exists(matches[0]):
            return matches[0]

    return None


class DownloadTask:
    """Represents a single download job."""

    def __init__(
        self,
        url: str,
        download_type: str = "audio",  # 'audio' or 'video'
        format_name: str = "mp3",  # 'mp3', 'opus', 'm4a', 'flac', 'best', '1080p', '720p'
        quality: str = "320",
        output_dir: Optional[str] = None,
        embed_metadata: bool = True,
        embed_thumbnail: bool = True,
    ):
        self.task_id = str(uuid.uuid4())[:8]
        self.url = url
        self.download_type = download_type
        self.format_name = format_name
        self.quality = quality
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation) or str(Path.home() / "Music")
        self.output_dir = output_dir or default_dir
        self.embed_metadata = embed_metadata
        self.embed_thumbnail = embed_thumbnail

        # Live state
        self.title = "Fetching info..."
        self.artist = "Unknown Artist"
        self.thumbnail_url = ""
        self.duration_str = ""
        self.progress_percent = 0.0
        self.speed_str = "0 KB/s"
        self.eta_str = "--:--"
        self.downloaded_bytes_str = "0 MB"
        self.total_bytes_str = "0 MB"
        self.status = "queued"  # queued, downloading, converting, finished, error, cancelled
        self.final_filepath: Optional[str] = None
        self.error_message: Optional[str] = None


class DownloaderWorker(QThread):
    """
    Background worker thread executing yt-dlp extraction and download pipeline.
    """

    # Signals
    task_started = pyqtSignal(str)  # task_id
    progress_updated = pyqtSignal(str, float, str, str, str, str, str)  # id, %, speed, eta, downloaded, total, status
    task_finished = pyqtSignal(str, str, bool, str)  # id, filepath, success, error_msg

    def __init__(self, task: DownloadTask, parent=None):
        super().__init__(parent)
        self.task = task
        self._is_cancelled = False

    def cancel(self):
        """Signals the download process to abort."""
        self._is_cancelled = True
        self.task.status = "cancelled"

    def run(self):
        task = self.task
        task.status = "downloading"
        self.task_started.emit(task.task_id)

        # Ensure output directory exists
        Path(task.output_dir).mkdir(parents=True, exist_ok=True)
        out_tmpl = os.path.join(task.output_dir, "%(title)s.%(ext)s")

        ffmpeg_exe = get_ffmpeg_path()

        # Configure yt-dlp parameters
        ydl_opts: Dict[str, Any] = {
            "outtmpl": out_tmpl,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "progress_hooks": [self._progress_hook],
            "nocheckcertificate": True,
            "noplaylist": True,
        }

        if ffmpeg_exe:
            ydl_opts["ffmpeg_location"] = ffmpeg_exe

        postprocessors: List[Dict[str, Any]] = []

        if task.download_type == "audio":
            if ffmpeg_exe:
                ydl_opts["format"] = "bestaudio/best"
                audio_format = task.format_name.lower()
                audio_quality = task.quality if task.quality in ("320", "256", "192", "128") else "320"

                postprocessors.append({
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format if audio_format in ("mp3", "opus", "m4a", "flac") else "mp3",
                    "preferredquality": audio_quality,
                })

                if task.embed_metadata:
                    postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
                if task.embed_thumbnail and audio_format in ("mp3", "m4a", "flac"):
                    ydl_opts["writethumbnail"] = True
                    postprocessors.append({"key": "EmbedThumbnail"})
            else:
                # Direct audio stream download when ffmpeg is not available
                ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"

        else:
            # Video download
            if ffmpeg_exe:
                res_map = {
                    "best": "bestvideo+bestaudio/best",
                    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
                }
                ydl_opts["format"] = res_map.get(task.format_name, "bestvideo+bestaudio/best")
                ydl_opts["merge_output_format"] = "mp4"

                if task.embed_metadata:
                    postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
                if task.embed_thumbnail:
                    ydl_opts["writethumbnail"] = True
                    postprocessors.append({"key": "EmbedThumbnail"})
            else:
                # Direct single stream download
                ydl_opts["format"] = "best[ext=mp4]/best"

        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Pre-fetch info to get clean title and thumbnail
                info = ydl.extract_info(task.url, download=False)
                if info:
                    task.title = info.get("title", "Unknown Title")
                    task.artist = info.get("artist") or info.get("uploader") or "Unknown Artist"
                    task.thumbnail_url = info.get("thumbnail", "")

                if self._is_cancelled:
                    self.task_finished.emit(task.task_id, "", False, "Download cancelled by user.")
                    return

                # Perform actual download
                download_result = ydl.extract_info(task.url, download=True)
                
                # Determine final filename
                final_file = ""
                if download_result:
                    if "_filename" in download_result:
                        final_file = download_result["_filename"]
                    else:
                        expected = ydl.prepare_filename(download_result)
                        final_file = expected
                        if task.download_type == "audio" and ffmpeg_exe:
                            base, _ = os.path.splitext(expected)
                            final_file = f"{base}.{task.format_name}"
                        elif task.download_type == "video" and ffmpeg_exe:
                            base, _ = os.path.splitext(expected)
                            final_file = f"{base}.mp4"

                task.final_filepath = final_file
                task.status = "finished"
                task.progress_percent = 100.0
                self.progress_updated.emit(
                    task.task_id, 100.0, "--", "00:00",
                    task.total_bytes_str, task.total_bytes_str, "finished"
                )
                self.task_finished.emit(task.task_id, final_file, True, "")

        except Exception as e:
            err_msg = str(e)
            task.status = "error"
            task.error_message = err_msg
            self.task_finished.emit(task.task_id, "", False, err_msg)

    def _progress_hook(self, d: Dict[str, Any]):
        """Hook called by yt-dlp during download chunks and postprocessing."""
        if self._is_cancelled:
            raise Exception("Download cancelled by user.")

        status = d.get("status", "")
        task = self.task

        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0

            percent = (downloaded / total * 100) if total > 0 else 0.0
            task.progress_percent = percent

            def _format_bytes(b: float) -> str:
                if b >= 1024 * 1024 * 1024:
                    return f"{b / (1024**3):.2f} GB"
                if b >= 1024 * 1024:
                    return f"{b / (1024**2):.1f} MB"
                return f"{b / 1024:.0f} KB"

            def _format_eta(secs: int) -> str:
                if not secs or secs < 0:
                    return "--:--"
                m, s = divmod(int(secs), 60)
                h, m = divmod(m, 60)
                if h > 0:
                    return f"{h}:{m:02d}:{s:02d}"
                return f"{m:02d}:{s:02d}"

            task.speed_str = f"{_format_bytes(speed)}/s" if speed else "0 KB/s"
            task.eta_str = _format_eta(eta)
            task.downloaded_bytes_str = _format_bytes(downloaded)
            task.total_bytes_str = _format_bytes(total) if total else "Unknown"
            task.status = "downloading"

            self.progress_updated.emit(
                task.task_id,
                percent,
                task.speed_str,
                task.eta_str,
                task.downloaded_bytes_str,
                task.total_bytes_str,
                "downloading",
            )

        elif status == "finished":
            task.status = "converting"
            self.progress_updated.emit(
                task.task_id,
                99.0,
                "--",
                "--",
                task.total_bytes_str,
                task.total_bytes_str,
                "converting",
            )


class DownloadManager(QObject):
    """
    Central manager for queuing and executing download tasks.
    """

    task_added = pyqtSignal(DownloadTask)
    task_progress = pyqtSignal(str, float, str, str, str, str, str)
    task_completed = pyqtSignal(str, str, bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks: Dict[str, DownloadTask] = {}
        self.workers: Dict[str, DownloaderWorker] = {}
        self._mutex = QMutex()

    def start_download(
        self,
        url: str,
        download_type: str = "audio",
        format_name: str = "mp3",
        quality: str = "320",
        output_dir: Optional[str] = None,
        embed_metadata: bool = True,
        embed_thumbnail: bool = True,
    ) -> DownloadTask:
        """Creates and starts a new download task."""
        with QMutexLocker(self._mutex):
            task = DownloadTask(
                url=url,
                download_type=download_type,
                format_name=format_name,
                quality=quality,
                output_dir=output_dir,
                embed_metadata=embed_metadata,
                embed_thumbnail=embed_thumbnail,
            )
            self.tasks[task.task_id] = task

            worker = DownloaderWorker(task, self)
            worker.progress_updated.connect(self._on_worker_progress)
            worker.task_finished.connect(self._on_worker_finished)
            self.workers[task.task_id] = worker

            self.task_added.emit(task)
            worker.start()
            return task

    def cancel_task(self, task_id: str):
        """Cancels an active download task."""
        with QMutexLocker(self._mutex):
            worker = self.workers.get(task_id)
            if worker and worker.isRunning():
                worker.cancel()

    def _on_worker_progress(self, task_id, percent, speed, eta, downloaded, total, status):
        self.task_progress.emit(task_id, percent, speed, eta, downloaded, total, status)

    def _on_worker_finished(self, task_id, filepath, success, err_msg):
        with QMutexLocker(self._mutex):
            if task_id in self.workers:
                worker = self.workers.pop(task_id)
                worker.wait(1000)
        self.task_completed.emit(task_id, filepath, success, err_msg)


# Global download manager instance
download_manager = DownloadManager()
