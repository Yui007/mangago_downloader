"""
Controller classes that interface between the GUI and existing core modules.
These controllers handle all business logic without modifying the core application.
"""

import os
import sys
from typing import List, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import QApplication

# Add src to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.search import search_manga, get_manga_details
from src.downloader import ChapterDownloader, fetch_chapter_image_urls, get_chapter_list, close_driver
from src.converter import convert_manga_chapters
from src.models import Manga, Chapter, SearchResult, DownloadResult
from src.utils import sanitize_filename


class SearchWorker(QThread):
    """Worker thread for search operations."""
    
    search_completed = pyqtSignal(list)  # List[SearchResult]
    search_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, query: str, page: int = 1):
        super().__init__()
        self.query = query
        self.page = page
    
    def run(self):
        try:
            results = search_manga(self.query, self.page)
            self.search_completed.emit(results)
        except Exception as e:
            self.search_failed.emit(str(e))


class MangaDetailsWorker(QThread):
    """Worker thread for fetching manga details."""
    
    details_completed = pyqtSignal(object, object)  # Manga, WebDriver
    details_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, manga_url: str):
        super().__init__()
        self.manga_url = manga_url
    
    def run(self):
        try:
            manga, driver = get_manga_details(self.manga_url)
            self.details_completed.emit(manga, driver)
        except Exception as e:
            self.details_failed.emit(str(e))


class ChapterListWorker(QThread):
    """Worker thread for fetching chapter list."""
    
    chapters_completed = pyqtSignal(list)  # List[Chapter]
    chapters_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
    
    def run(self):
        try:
            chapters = get_chapter_list(self.driver)
            self.chapters_completed.emit(chapters)
        except Exception as e:
            self.chapters_failed.emit(str(e))
        finally:
            if self.driver:
                close_driver(self.driver)


class ImageUrlsWorker(QThread):
    """Worker thread for fetching chapter image URLs."""
    
    urls_completed = pyqtSignal(object, list)  # Chapter, List[str]
    urls_failed = pyqtSignal(object, str)  # Chapter, Error message
    progress_updated = pyqtSignal(int)  # Progress value
    
    def __init__(self, chapters: List[Chapter]):
        super().__init__()
        self.chapters = chapters
    
    def run(self):
        for i, chapter in enumerate(self.chapters):
            try:
                image_urls = fetch_chapter_image_urls(chapter.url)
                chapter.image_urls = image_urls
                self.urls_completed.emit(chapter, image_urls)
            except Exception as e:
                self.urls_failed.emit(chapter, str(e))
            
            self.progress_updated.emit(i + 1)


class DownloadWorker(QThread):
    """Worker thread for downloading chapters."""
    
    download_completed = pyqtSignal(object)  # DownloadResult
    download_failed = pyqtSignal(object, str)  # Chapter, Error message
    progress_updated = pyqtSignal(int)  # Progress value
    status_updated = pyqtSignal(str)  # Status message
    
    def __init__(self, manga: Manga, chapters: List[Chapter], max_workers: int = 5, download_config: Optional[dict] = None):
        super().__init__()
        self.manga = manga
        self.chapters = chapters
        self.max_workers = max_workers
        self.download_config = download_config or {}
        self.downloader = None
    
    def run(self):
        try:
            # Get download directory from config, with fallback to default
            download_dir = self.download_config.get("download_location", "downloads")
            self.downloader = ChapterDownloader(max_workers=self.max_workers, download_dir=download_dir)
            
            for i, chapter in enumerate(self.chapters):
                self.status_updated.emit(f"Downloading Chapter {chapter.number}...")
                try:
                    result = self.downloader.download_chapter(self.manga, chapter)
                    self.download_completed.emit(result)
                except Exception as e:
                    self.download_failed.emit(chapter, str(e))
                
                self.progress_updated.emit(i + 1)
            
        except Exception as e:
            self.status_updated.emit(f"Download failed: {str(e)}")
        finally:
            if self.downloader:
                self.downloader.close()


class ConversionWorker(QThread):
    """Worker thread for converting downloaded chapters."""
    
    conversion_completed = pyqtSignal(list)  # List[str] - created files
    conversion_failed = pyqtSignal(str)  # Error message
    progress_updated = pyqtSignal(int)  # Progress value
    status_updated = pyqtSignal(str)  # Status message
    
    def __init__(self, manga_dir: str, format_type: str, delete_images: bool = False):
        super().__init__()
        self.manga_dir = manga_dir
        self.format_type = format_type
        self.delete_images = delete_images
    
    def run(self):
        try:
            self.status_updated.emit(f"Converting to {self.format_type.upper()}...")
            created_files = convert_manga_chapters(
                self.manga_dir, 
                self.format_type, 
                self.delete_images
            )
            self.conversion_completed.emit(created_files)
        except Exception as e:
            self.conversion_failed.emit(str(e))


class SearchController(QObject):
    """Controller for search operations."""
    
    search_started = pyqtSignal()
    search_completed = pyqtSignal(list)  # List[SearchResult]
    search_failed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.worker = None
    
    def search_manga(self, query: str, page: int = 1):
        """Search for manga by title."""
        if self.worker and self.worker.isRunning():
            return
        
        self.search_started.emit()
        self.worker = SearchWorker(query, page)
        self.worker.search_completed.connect(self.search_completed.emit)
        self.worker.search_failed.connect(self.search_failed.emit)
        self.worker.start()


class MangaController(QObject):
    """Controller for manga details and chapters."""
    
    details_started = pyqtSignal()
    details_completed = pyqtSignal(object)  # Manga
    chapters_completed = pyqtSignal(list)  # List[Chapter]
    operation_failed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.details_worker = None
        self.chapters_worker = None
        self.current_manga = None
    
    def get_manga_details(self, manga_url: str):
        """Get manga details and chapters."""
        if self.details_worker and self.details_worker.isRunning():
            return
        
        self.details_started.emit()
        self.details_worker = MangaDetailsWorker(manga_url)
        self.details_worker.details_completed.connect(self._on_details_completed)
        self.details_worker.details_failed.connect(self.operation_failed.emit)
        self.details_worker.start()
    
    def _on_details_completed(self, manga: Manga, driver):
        """Handle manga details completion and fetch chapters."""
        self.current_manga = manga
        self.details_completed.emit(manga)
        
        # Now fetch chapters using the driver
        self.chapters_worker = ChapterListWorker(driver)
        self.chapters_worker.chapters_completed.connect(self.chapters_completed.emit)
        self.chapters_worker.chapters_failed.connect(self.operation_failed.emit)
        self.chapters_worker.start()


class DownloadController(QObject):
    """Controller for download operations."""
    
    download_started = pyqtSignal()
    urls_progress = pyqtSignal(int, int)  # current, total
    urls_completed = pyqtSignal()
    download_progress = pyqtSignal(int, int)  # current, total
    download_completed = pyqtSignal(list)  # List[DownloadResult]
    chapter_downloaded = pyqtSignal(object)  # DownloadResult
    operation_failed = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.urls_worker = None
        self.download_worker = None
        self.results = []
    
    def download_chapters(self, manga: Manga, chapters: List[Chapter], max_workers: int = 5, download_config: Optional[dict] = None):
        """Download selected chapters."""
        if (self.urls_worker and self.urls_worker.isRunning()) or \
           (self.download_worker and self.download_worker.isRunning()):
            return
        
        self.results = []
        self.download_started.emit()
        
        # First, fetch image URLs for all chapters
        self._fetch_image_urls(chapters, manga, max_workers, download_config)
    
    def _fetch_image_urls(self, chapters: List[Chapter], manga: Manga, max_workers: int, download_config: Optional[dict] = None):
        """Fetch image URLs for chapters."""
        self.status_updated.emit("Fetching image URLs...")
        self.urls_worker = ImageUrlsWorker(chapters)
        self.urls_worker.urls_completed.connect(self._on_urls_completed)
        self.urls_worker.urls_failed.connect(self._on_urls_failed)
        self.urls_worker.progress_updated.connect(
            lambda current: self.urls_progress.emit(current, len(chapters))
        )
        self.urls_worker.finished.connect(
            lambda: self._start_downloads(manga, chapters, max_workers, download_config)
        )
        self.urls_worker.start()
    
    def _on_urls_completed(self, chapter: Chapter, urls: List[str]):
        """Handle successful URL fetching."""
        self.status_updated.emit(f"Found {len(urls)} images for Chapter {chapter.number}")
    
    def _on_urls_failed(self, chapter: Chapter, error: str):
        """Handle failed URL fetching."""
        self.status_updated.emit(f"Failed to get URLs for Chapter {chapter.number}: {error}")
    
    def _start_downloads(self, manga: Manga, chapters: List[Chapter], max_workers: int, download_config: Optional[dict] = None):
        """Start the actual downloads."""
        self.urls_completed.emit()
        self.status_updated.emit("Starting downloads...")
        
        # Filter chapters that have image URLs
        valid_chapters = [ch for ch in chapters if ch.image_urls]
        
        if not valid_chapters:
            self.operation_failed.emit("No valid chapters to download")
            return
        
        self.download_worker = DownloadWorker(manga, valid_chapters, max_workers, download_config)
        self.download_worker.download_completed.connect(self._on_download_completed)
        self.download_worker.download_failed.connect(self._on_download_failed)
        self.download_worker.progress_updated.connect(
            lambda current: self.download_progress.emit(current, len(valid_chapters))
        )
        self.download_worker.status_updated.connect(self.status_updated.emit)
        self.download_worker.finished.connect(
            lambda: self.download_completed.emit(self.results)
        )
        self.download_worker.start()
    
    def _on_download_completed(self, result: DownloadResult):
        """Handle successful chapter download."""
        self.results.append(result)
        self.chapter_downloaded.emit(result)
    
    def _on_download_failed(self, chapter: Chapter, error: str):
        """Handle failed chapter download."""
        result = DownloadResult(
            chapter=chapter,
            success=False,
            error_message=error
        )
        self.results.append(result)
        self.chapter_downloaded.emit(result)


class ConversionController(QObject):
    """Controller for conversion operations."""
    
    conversion_started = pyqtSignal()
    conversion_completed = pyqtSignal(list)  # List[str] - created files
    conversion_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.worker = None
    
    def convert_chapters(self, manga: Manga, format_type: str, delete_images: bool = False):
        """Convert downloaded chapters to specified format."""
        if self.worker and self.worker.isRunning():
            return
        
        manga_dir = os.path.join("downloads", sanitize_filename(manga.title))
        
        self.conversion_started.emit()
        self.worker = ConversionWorker(manga_dir, format_type, delete_images)
        self.worker.conversion_completed.connect(self.conversion_completed.emit)
        self.worker.conversion_failed.connect(self.conversion_failed.emit)
        self.worker.progress_updated.connect(self.progress_updated.emit)
        self.worker.status_updated.connect(self.status_updated.emit)
        self.worker.start()