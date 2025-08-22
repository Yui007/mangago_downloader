"""
Downloader engine with threading support for the Mangago Downloader.
"""
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from .models import Chapter, Manga, DownloadResult
from .utils import SessionManager, NetworkError, ParsingError, DownloadError, create_directory, sanitize_filename


class ChapterDownloader:
    """
    Handles downloading of manga chapters with threading support.
    """
    
    def __init__(self, max_workers: int = 5, download_dir: str = "downloads"):
        """
        Initialize the chapter downloader.
        
        Args:
            max_workers (int): Maximum number of concurrent threads.
            download_dir (str): Base directory for downloads.
        """
        self.max_workers = max_workers
        self.download_dir = download_dir
        self.session = SessionManager()
        
    def download_chapter(self, manga: Manga, chapter: Chapter) -> DownloadResult:
        """
        Download a single chapter.
        
        Args:
            manga (Manga): The manga the chapter belongs to.
            chapter (Chapter): The chapter to download.
            
        Returns:
            DownloadResult: Result of the download operation.
        """
        try:
            # Create directory for manga
            manga_dir = os.path.join(self.download_dir, sanitize_filename(manga.title))
            if not create_directory(manga_dir):
                return DownloadResult(
                    chapter=chapter,
                    success=False,
                    error_message=f"Failed to create directory for manga: {manga.title}"
                )
            
            # Create directory for chapter
            chapter_dir = os.path.join(manga_dir, f"Chapter_{chapter.number}")
            if not create_directory(chapter_dir):
                return DownloadResult(
                    chapter=chapter,
                    success=False,
                    error_message=f"Failed to create directory for chapter: {chapter.number}"
                )
            
            # Get image URLs if not already present
            if not chapter.image_urls:
                chapter.image_urls = self._get_chapter_image_urls(chapter.url)
            
            # Download images
            downloaded_count = 0
            for i, image_url in enumerate(chapter.image_urls, start=1):
                image_filename = f"{i:03d}.jpg"  # Use 3-digit numbering (001.jpg, 002.jpg, etc.)
                image_path = os.path.join(chapter_dir, image_filename)
                
                if self._download_image(image_url, image_path):
                    downloaded_count += 1
            
            return DownloadResult(
                chapter=chapter,
                success=True,
                file_path=chapter_dir,
                images_downloaded=downloaded_count
            )
        except Exception as e:
            return DownloadResult(
                chapter=chapter,
                success=False,
                error_message=str(e)
            )
    
    def download_chapters(self, manga: Manga, chapters: List[Chapter]) -> List[DownloadResult]:
        """
        Download multiple chapters using threading.
        
        Args:
            manga (Manga): The manga the chapters belong to.
            chapters (List[Chapter]): List of chapters to download.
            
        Returns:
            List[DownloadResult]: Results of the download operations.
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_chapter = {
                executor.submit(self.download_chapter, manga, chapter): chapter
                for chapter in chapters
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chapter):
                chapter = future_to_chapter[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    result = DownloadResult(
                        chapter=chapter,
                        success=False,
                        error_message=f"Unexpected error: {str(e)}"
                    )
                    results.append(result)
        
        return results
    
    def _get_chapter_image_urls(self, chapter_url: str) -> List[str]:
        """
        Extract all image URLs from a paginated chapter.
        """
        if not chapter_url:
            raise ParsingError("Chapter URL is invalid.")

        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        image_urls = []
        try:
            driver.get(chapter_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "multi_pg_tip")))

            # The most reliable way to get all page URLs is from the dropdown menu.
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            page_urls = []
            dropdown_menu = soup.select_one("ul#dropdown-menu-page")
            
            if not dropdown_menu:
                raise ParsingError("Could not find the chapter page dropdown menu.")

            # The most reliable way is to get all page URLs from the dropdown.
            for item in dropdown_menu.select("li a"):
                href = item.get('href')
                if href and isinstance(href, str):
                    full_url = urljoin(chapter_url, href)
                    if full_url not in page_urls:
                        page_urls.append(full_url)

            if not page_urls:
                 # Fallback if the dropdown parsing fails, get total pages from text
                 page_tip = soup.select_one(".multi_pg_tip")
                 if not page_tip:
                     raise ParsingError("Could not find page count for chapter.")
                 match = re.search(r'\((\d+)/(\d+)\)', page_tip.get_text())
                 if not match:
                      raise ParsingError("Could not parse page count from chapter.")
                 total_pages = int(match.group(2))
                 # Reconstruct URLs manually as a last resort
                 base_url = chapter_url.rsplit('/', 2)[0]
                 for i in range(1, total_pages + 1):
                      page_urls.append(f"{base_url}/{i}/")


            # Visit each page URL and extract the main image source.
            for page_url in sorted(list(set(page_urls))):
                driver.get(page_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "page1")))
                
                page_soup = BeautifulSoup(driver.page_source, 'html.parser')
                img_tag = page_soup.select_one("img#page1")

                if img_tag:
                    src = img_tag.get("src")
                    if src and isinstance(src, str):
                        image_urls.append(src)
                    else:
                        print(f"Warning: Found img#page1 but 'src' was invalid on {page_url}")
                else:
                    print(f"Warning: Could not find image with id 'page1' on page {page_url}")

            return image_urls
        except (TimeoutException, WebDriverException) as e:
            raise NetworkError(f"Selenium error while getting image URLs: {e}")
        except Exception as e:
            raise ParsingError(f"Failed to parse image URLs: {e}")
        finally:
            driver.quit()
    
    def _is_image_url(self, url: str) -> bool:
        """
        Check if a URL points to an image.
        
        Args:
            url (str): URL to check.
            
        Returns:
            bool: True if URL points to an image, False otherwise.
        """
        # Check file extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        return any(path.endswith(ext) for ext in image_extensions)
    
    def _download_image(self, image_url: str, image_path: str) -> bool:
        """
        Download a single image.
        
        Args:
            image_url (str): URL of the image to download.
            image_path (str): Path where the image should be saved.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        try:
            # Skip if file already exists
            if os.path.exists(image_path):
                return True
            
            response = self.session.get(image_url)
            response.raise_for_status()
            
            # Save image
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"Failed to download image {image_url}: {e}")
            return False
    
    def close(self):
        """
        Close the session.
        """
        self.session.close()


def get_chapter_list(driver: webdriver.Chrome) -> List[Chapter]:
    """
    Get the list of chapters for a given manga from an existing driver instance.
    
    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance with the manga page loaded.
        
    Returns:
        List[Chapter]: List of chapters.
    """
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        chapter_table = soup.find('table', class_='listing')
        if not isinstance(chapter_table, Tag):
            raise DownloadError("Could not find chapter table.")
        
        chapters = []
        for row in chapter_table.find_all('tr'):
            link = row.find('a', class_='chico')
            if not link:
                continue

            title = link.get_text(strip=True)
            url = link.get('href')

            if url and not url.startswith('http'):
                url = urljoin(driver.current_url, url)

            import re
            match = re.search(r'Ch\.(\d+(\.\d+)?)', title)
            number = float(match.group(1)) if match else 0

            chapters.append(Chapter(
                number=int(number),
                title=title,
                url=url
            ))
        
        # The chapters are usually listed from newest to oldest, so we reverse
        return sorted(chapters, key=lambda ch: ch.number)
    except Exception as e:
        raise DownloadError(f"Failed to get chapter list: {e}")


def close_driver(driver: webdriver.Chrome):
    """Safely closes the WebDriver."""
    if driver:
        try:
            driver.quit()
        except Exception:
            pass # Ignore errors on quit


def _extract_chapter_number(href: str, text: str) -> float:
    """
    Extract chapter number from href or text.
    
    Args:
        href (str): Chapter URL.
        text (str): Chapter link text.
        
    Returns:
        float: Chapter number.
    """
    # Try to extract from href first
    match = re.search(r'chapter[-_]?(\d+\.?\d*)', href, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # Try to extract from text
    match = re.search(r'(?:chapter|ch\.?)\s*(\d+\.?\d*)', text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # Default to 0 if we can't extract
    return 0.0


def download_manga_chapters(
    manga: Manga,
    chapters: Union[List[Chapter], Chapter, str],
    max_workers: int = 5,
    download_dir: str = "downloads"
) -> List[DownloadResult]:
    """
    Download manga chapters.
    
    Args:
        manga (Manga): The manga to download.
        chapters (Union[List[Chapter], Chapter, str]): Chapters to download.
            Can be a list of Chapter objects, a single Chapter, or a string
            specifying "all" to download all chapters.
        max_workers (int): Maximum number of concurrent threads.
        download_dir (str): Base directory for downloads.
        
    Returns:
        List[DownloadResult]: Results of the download operations.
    """
    # The chapter list is now always provided directly.
    chapter_list: List[Chapter] = []
    if isinstance(chapters, Chapter):
        chapter_list = [chapters]
    elif isinstance(chapters, list):
        chapter_list = chapters
    else:
        print(f"Invalid chapters parameter type: {type(chapters)}")
        return []

    # Create downloader and download chapters
    downloader = ChapterDownloader(max_workers=max_workers, download_dir=download_dir)
    try:
        results = downloader.download_chapters(manga, chapter_list)
        return results
    finally:
        downloader.close()