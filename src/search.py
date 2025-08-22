"""
Search functionality for the Mangago Downloader.
"""
import urllib.parse
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
import httpx
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from .models import Manga, SearchResult
from .utils import SessionManager, NetworkError, ParsingError


# Base URL for Mangago
BASE_URL = "https://www.mangago.me/"
SEARCH_URL = "https://www.mangago.me/r/l_search/"


def search_manga(query: str, page: int = 1) -> List[SearchResult]:
    """
    Search for manga by title using Selenium to avoid 403 errors.
    
    Args:
        query (str): The search query.
        page (int): The page number for pagination (default: 1).
        
    Returns:
        List[SearchResult]: List of search results.
        
    Raises:
        NetworkError: If there's a network-related error.
        ParsingError: If there's an error parsing the response.
    """
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        # Initialize the WebDriver
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Encode the query for URL
        encoded_query = urllib.parse.quote_plus(query)
        
        # Construct search URL
        search_url = f"{SEARCH_URL}?name={encoded_query}&page={page}"
        
        # Navigate to the search page
        driver.get(search_url)
        
        # Wait for the search results to load
        time.sleep(7)
        
        # Get the page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract search results
        results = _parse_search_results(soup)
        
        return results
    except TimeoutException as e:
        raise NetworkError(f"Timeout while searching for manga: {str(e)}")
    except WebDriverException as e:
        raise NetworkError(f"WebDriver error while searching for manga: {str(e)}")
    except Exception as e:
        raise ParsingError(f"Failed to parse search results: {str(e)}")
    finally:
        # Close the WebDriver
        if driver:
            driver.quit()


def _parse_search_results(soup: BeautifulSoup) -> List[SearchResult]:
    """
    Parse search results from BeautifulSoup object.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content.
        
    Returns:
        List[SearchResult]: List of parsed search results.
    """
    results = []
    
    for index, li in enumerate(soup.select("#search_list li"), start=1):
        try:
            manga = _parse_manga_item(li)
            if manga:
                search_result = SearchResult(index=index, manga=manga)
                results.append(search_result)
        except Exception as e:
            # Skip items that fail to parse
            print(f"Warning: Failed to parse manga item {index}: {e}")
            continue
    
    return results


def _parse_manga_item(item) -> Optional[Manga]:
    """
    Parse a single manga item from search results.
    
    Args:
        item: BeautifulSoup element representing a manga item.
        
    Returns:
        Optional[Manga]: Parsed Manga object or None if parsing fails.
    """
    title_tag = item.select_one("h2 a")
    if not title_tag:
        return None

    title = title_tag.get_text(strip=True)
    url = title_tag.get("href")

    if not title or not url:
        return None
        
    # Make sure URL is absolute
    if url.startswith('/'):
        url = BASE_URL.rstrip('/') + url

    manga = Manga(title=title, url=url)

    author = item.select_one(".row-3.gray")
    author_text = author.get_text(strip=True) if author else ""
    manga.author = author_text.replace("Author:", "").strip()

    genres = item.select_one(".row-4.blue .gray")
    genres_text = genres.get_text(strip=True) if genres else ""
    manga.genres = [g.strip() for g in genres_text.split(',') if g.strip()] if genres_text else []

    latest_chapter_tag = item.select_one(".row-5.gray a.chico")
    if latest_chapter_tag:
        chapter_text = latest_chapter_tag.get_text(strip=True)
        import re
        match = re.search(r'(\d+(\.\d+)?)', chapter_text)
        if match:
            manga.total_chapters = int(float(match.group(1)))
        else:
            manga.total_chapters = 0
    else:
        manga.total_chapters = 0


    return manga


def get_manga_details(manga_url: str) -> Tuple[Manga, webdriver.Chrome]:
    """
    Get detailed information about a specific manga using Selenium.
    
    Args:
        manga_url (str): The URL of the manga.
        
    Returns:
        Manga: Manga object with detailed information.
        
    Raises:
        NetworkError: If there's a network-related error.
        ParsingError: If there's an error parsing the response.
    """
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    # Run in non-headless mode to avoid 403 errors
    # Comment out the next line if you want to run in headless mode
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        # Initialize the WebDriver
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Navigate to the manga page
        driver.get(manga_url)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "page")))
        
        # Get the page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract manga details
        manga = _parse_manga_details(soup, manga_url)
        
        return manga, driver
    except TimeoutException as e:
        raise NetworkError(f"Timeout while getting manga details: {str(e)}")
    except WebDriverException as e:
        raise NetworkError(f"WebDriver error while getting manga details: {str(e)}")
    except Exception as e:
        raise ParsingError(f"Failed to parse manga details: {str(e)}")
    # Do not close the driver here, it will be closed by the caller


def _parse_manga_details(soup: BeautifulSoup, manga_url: str) -> Manga:
    """
    Parse detailed manga information from BeautifulSoup object.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content.
        manga_url (str): The URL of the manga.
        
    Returns:
        Manga: Manga object with detailed information.
    """
    try:
        # Extract title
        title_elem = soup.find('h1') or soup.find('div', class_='title')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        manga = Manga(title=title, url=manga_url)
        
        # Try to extract author
        author_elem = soup.find('span', class_='author') or soup.find('div', class_='author-info')
        if author_elem:
            manga.author = author_elem.get_text(strip=True)
        
        # Try to extract genres
        genre_container = soup.find('div', class_='genres') or soup.find('div', class_='genre-list')
        if genre_container and isinstance(genre_container, Tag):
            genre_elems = genre_container.find_all('a') or genre_container.find_all('span')
            manga.genres = [elem.get_text(strip=True) for elem in genre_elems]
        
        # Try to extract cover image
        cover_elem = soup.find('img', class_='cover') or soup.find('img', {'id': 'cover'})
        # Check if cover_elem is a Tag object before accessing attributes
        if cover_elem and not isinstance(cover_elem, str):
            src = cover_elem.get('src') if hasattr(cover_elem, 'get') else None
            if src:
                manga.cover_image_url = str(src)
        
        return manga
    except Exception as e:
        print(f"Warning: Failed to parse manga details: {e}")
        # Return basic manga object even if parsing details fails
        return Manga(title="Unknown Title", url=manga_url)