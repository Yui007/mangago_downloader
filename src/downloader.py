"""
Downloader engine with threading support for the Mangago Downloader.
"""
import os
import re
import threading
import time
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
        self.max_workers = max_workers
        self.download_dir = download_dir
        self.session = SessionManager()
        
    def download_chapter(self, manga: Manga, chapter: Chapter) -> DownloadResult:
        if not chapter.image_urls:
            return DownloadResult(chapter=chapter, success=False, error_message="No image URLs found.")

        manga_dir = os.path.join(self.download_dir, sanitize_filename(manga.title))
        create_directory(manga_dir)
        
        chapter_dir = os.path.join(manga_dir, f"Chapter_{chapter.number}")
        create_directory(chapter_dir)
        
        downloaded_count = 0
        for i, image_url in enumerate(chapter.image_urls, start=1):
            image_filename = f"{i:03d}.jpg"
            image_path = os.path.join(chapter_dir, image_filename)
            if self._download_image(image_url, image_path):
                downloaded_count += 1
        
        return DownloadResult(
            chapter=chapter,
            success=True,
            file_path=chapter_dir,
            images_downloaded=downloaded_count
        )
    
    def download_chapters(self, manga: Manga, chapters: List[Chapter]) -> List[DownloadResult]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_chapter = {executor.submit(self.download_chapter, manga, chapter): chapter for chapter in chapters}
            for future in as_completed(future_to_chapter):
                results.append(future.result())
        return results
    
    def _download_image(self, image_url: str, image_path: str) -> bool:
        try:
            if os.path.exists(image_path):
                return True
            response = self.session.get(image_url, headers={"Referer": "https://www.mangago.me/"}, timeout=20)
            response.raise_for_status()
            with open(image_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception:
            return False
    
    def close(self):
        self.session.close()


def fetch_chapter_image_urls(chapter_url: str) -> List[str]:
    """
    Extract all image URLs from a paginated chapter using the fast, eager-loading strategy.
    """
    if not chapter_url:
        raise ParsingError("Chapter URL is invalid.")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.page_load_strategy = "eager"
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)

    img_urls = []
    try:
        driver.get(chapter_url)
        
        page_info_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".multi_pg_tip.left"))
        )
        page_info = page_info_element.text
        total_pages = int(page_info.split("/")[-1].replace(")", ""))
        
        for i in range(1, total_pages + 1):
            url = chapter_url if i == 1 else f"{chapter_url.rstrip('/')}/{i}/"
            if driver.current_url != url:
                driver.get(url)

            img = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"img#page{i}"))
            )
            img_url = img.get_attribute("src")
            if img_url:
                img_urls.append(img_url)
        
        return img_urls
    finally:
        driver.quit()


def get_chapter_list(driver: webdriver.Chrome) -> List[Chapter]:
    """
    Get the list of chapters for a given manga from an existing driver instance.
    """
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

        match = re.search(r'Ch\.(\d+(\.\d+)?)', title)
        number = float(match.group(1)) if match else 0
        
        chapters.append(Chapter(number=int(number), title=title, url=url))
    
    return sorted(chapters, key=lambda ch: ch.number)


def close_driver(driver: webdriver.Chrome):
    """Safely closes the WebDriver."""
    if driver:
        try:
            driver.quit()
        except Exception:
            pass