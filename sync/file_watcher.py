"""
文件监听服务 - 监听Obsidian Vault文件变更
"""

import time
import logging
from pathlib import Path
from typing import Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class ObsidianFileHandler(FileSystemEventHandler):
    """Obsidian文件变更处理器"""

    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory and event.src_path.endswith(".md"):
            self.callback("modified", event.src_path)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory and event.src_path.endswith(".md"):
            self.callback("created", event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory and event.src_path.endswith(".md"):
            self.callback("deleted", event.src_path)


class FileWatcher:
    """文件监听器"""

    def __init__(self, vault_path: str, callback: Optional[Callable[[str, str], None]] = None):
        self.vault_path = Path(vault_path)
        self.callback = callback or self._default_callback
        self._observer: Optional[Observer] = None

    def _default_callback(self, event_type: str, file_path: str):
        """默认回调"""
        logger.info(f"File {event_type}: {file_path}")

    def start(self):
        """启动监听"""
        if self._observer is not None:
            return

        self._observer = Observer()
        handler = ObsidianFileHandler(self.callback)
        self._observer.schedule(handler, str(self.vault_path), recursive=True)
        self._observer.start()
        logger.info(f"Started watching: {self.vault_path}")

    def stop(self):
        """停止监听"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped file watching")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
