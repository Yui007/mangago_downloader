"""
Search functionality for the Mangago Downloader.
"""
import urllib.parse
import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib.parse import urljoin

from .models import Manga, SearchResult
from .utils import SessionManager, NetworkError, ParsingError


# Base URL for Mangago
BASE_URL = "https://www.mangago.me/"
SEARCH_URL = "https://www.mangago.me/r/l_search/"


def search_manga(query: str, page: int = 1) -> List[SearchResult]:
    """
    Search for manga by title using the faster 'eager' page load strategy.
    """
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.page_load_strategy = "eager"
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)

    try:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"{SEARCH_URL}?name={encoded_query}&page={page}"
        driver.get(search_url)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search_list")))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return _parse_search_results(soup)
    finally:
        driver.quit()


def _parse_search_results(soup: BeautifulSoup) -> List[SearchResult]:
    results = []
    for index, li in enumerate(soup.select("#search_list li"), start=1):
        try:
            manga = _parse_manga_item(li)
            if manga:
                results.append(SearchResult(index=index, manga=manga))
        except Exception as e:
            print(f"Warning: Failed to parse a search result item: {e}")
            continue
    return results


def _parse_manga_item(item: Tag) -> Optional[Manga]:
    title_tag = item.select_one("h2 a")
    if not title_tag:
        return None

    title = title_tag.get_text(strip=True)
    url = title_tag.get("href")

    if not title or not isinstance(url, str):
        return None
        
    if url.startswith('/'):
        url = urljoin(BASE_URL, url)

    manga = Manga(title=title, url=url)

    author_text = (author.get_text(strip=True) if (author := item.select_one(".row-3.gray")) else "").replace("Author:", "").strip()
    manga.author = author_text

    genres_text = (genres.get_text(strip=True) if (genres := item.select_one(".row-4.blue .gray")) else "")
    manga.genres = [g.strip() for g in genres_text.split(',') if g.strip()]

    latest_chapter_tag = item.select_one(".row-5.gray a.chico")
    if latest_chapter_tag:
        chapter_text = latest_chapter_tag.get_text(strip=True)
        match = re.search(r'(\d+(\.\d+)?)', chapter_text)
        manga.total_chapters = int(float(match.group(1))) if match else 0
    else:
        manga.total_chapters = 0

    return manga


def get_manga_details(manga_url: str) -> Tuple[Manga, webdriver.Chrome]:
    """
    Get detailed manga info using the 'eager' page load strategy.
    The WebDriver instance is returned for reuse.
    """
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)
    
    driver.get(manga_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "page")))
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    manga = _parse_manga_details(soup, manga_url)
    
    return manga, driver


def _parse_manga_details(soup: BeautifulSoup, manga_url: str) -> Manga:
    title = (title_elem.get_text(strip=True) if (title_elem := soup.find('h1')) else "Unknown Title")
    manga = Manga(title=title, url=manga_url)

    author_elem = soup.find('span', class_='author') or soup.find('div', class_='author-info')
    if author_elem:
        manga.author = author_elem.get_text(strip=True)
    
    genre_container = soup.find('div', class_='genres') or soup.find('div', class_='genre-list')
    if isinstance(genre_container, Tag):
        manga.genres = [elem.get_text(strip=True) for elem in genre_container.find_all('a')]

    cover_elem = soup.find('img', class_='cover') or soup.find('img', {'id': 'cover'})
    if isinstance(cover_elem, Tag):
        src = cover_elem.get('src')
        if src and isinstance(src, str):
            manga.cover_image_url = src
    
    return manga