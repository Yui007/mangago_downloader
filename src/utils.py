"""
Utility functions and constants for the Mangago Downloader.
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from httpx import Response


# User agents for requests to avoid blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# Default headers for requests
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "Referer": "https://www.mangago.me/",
    "Accept-Charset": "utf-8"
}


def get_random_user_agent() -> str:
    """
    Get a random user agent from the list.
    
    Returns:
        str: A randomly selected user agent string.
    """
    return random.choice(USER_AGENTS)


def get_headers() -> Dict[str, str]:
    """
    Get headers with a random user agent for requests.
    
    Returns:
        Dict[str, str]: Headers dictionary with user agent.
    """
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = get_random_user_agent()
    return headers


class SessionManager:
    """
    Manages HTTP sessions for making requests.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the session manager.
        
        Args:
            timeout (int): Request timeout in seconds.
        """
        self.timeout = timeout
        self.session = httpx.Client(
            headers=get_headers(),
            timeout=timeout,
            follow_redirects=True
        )
    
    def get(self, url: str, **kwargs) -> Response:
        """
        Make a GET request.
        
        Args:
            url (str): The URL to request.
            **kwargs: Additional arguments to pass to the request.
            
        Returns:
            Response: The HTTP response.
        """
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Response:
        """
        Make a POST request.
        
        Args:
            url (str): The URL to request.
            **kwargs: Additional arguments to pass to the request.
            
        Returns:
            Response: The HTTP response.
        """
        return self.session.post(url, **kwargs)
    
    def close(self):
        """
        Close the session.
        """
        self.session.close()


def create_directory(path: str) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        path (str): The path to create.
        
    Returns:
        bool: True if directory was created or already exists, False otherwise.
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename (str): The filename to sanitize.
        
    Returns:
        str: The sanitized filename.
    """
    # Remove invalid characters for file names
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit filename length (255 is a common filesystem limit)
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename.strip()


def get_file_size(filepath: str) -> Optional[int]:
    """
    Get the size of a file in bytes.
    
    Args:
        filepath (str): The path to the file.
        
    Returns:
        Optional[int]: The size of the file in bytes, or None if file doesn't exist.
    """
    try:
        return os.path.getsize(filepath)
    except OSError:
        return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes (int): Size in bytes.
        
    Returns:
        str: Formatted file size.
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size_float = float(size_bytes)
    while size_float >= 1024.0 and i < len(size_names) - 1:
        size_float /= 1024.0
        i += 1
    
    return f"{size_float:.1f} {size_names[i]}"


# Error handling utilities
class MangaDownloaderError(Exception):
    """Base exception class for Manga Downloader errors."""
    pass


class NetworkError(MangaDownloaderError):
    """Exception raised for network-related errors."""
    pass


class ParsingError(MangaDownloaderError):
    """Exception raised for parsing-related errors."""
    pass


class DownloadError(MangaDownloaderError):
    """Exception raised for download-related errors."""
    pass