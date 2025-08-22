"""
Data models for the Mangago Downloader.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Manga:
    """
    Represents a manga with its metadata.
    """
    title: str
    url: str
    author: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    total_chapters: Optional[int] = None
    cover_image_url: Optional[str] = None
    
    def __str__(self) -> str:
        """
        String representation of the manga.
        
        Returns:
            str: Formatted string with manga title and author.
        """
        if self.author:
            return f"{self.title} by {self.author}"
        return self.title


@dataclass
class Chapter:
    """
    Represents a manga chapter.
    """
    number: float  # Using float to handle chapters like 1.5, 2.0, etc.
    url: str
    title: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """
        String representation of the chapter.
        
        Returns:
            str: Formatted string with chapter number and title.
        """
        if self.title:
            return f"Chapter {self.number}: {self.title}"
        return f"Chapter {self.number}"


@dataclass
class SearchResult:
    """
    Represents a search result containing manga information.
    """
    index: int
    manga: Manga
    
    def __str__(self) -> str:
        """
        String representation of the search result.
        
        Returns:
            str: Formatted string with index and manga information.
        """
        return f"{self.index}. {self.manga}"


@dataclass
class DownloadResult:
    """
    Represents the result of a download operation.
    """
    chapter: Chapter
    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    images_downloaded: int = 0
    
    def __str__(self) -> str:
        """
        String representation of the download result.
        
        Returns:
            str: Formatted string with download result information.
        """
        if self.success:
            return f"Successfully downloaded {self.chapter} to {self.file_path}"
        else:
            return f"Failed to download {self.chapter}: {self.error_message}"