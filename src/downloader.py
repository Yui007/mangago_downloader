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
import requests # Import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

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
            if self._download_image(image_url, image_path, chapter.url): # Pass chapter.url as referer
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
    
    def _download_image(self, image_url: str, image_path: str, chapter_referer: str) -> bool: # Add chapter_referer parameter
        try:
            if os.path.exists(image_path):
                return True
            # Determine the Referer based on the chapter_referer's domain
            parsed_chapter_referer = urlparse(chapter_referer)
            chapter_domain = parsed_chapter_referer.netloc

            if chapter_domain in ["www.youhim.me", "www.mangago.zone", "www.mangago.me"]:
                # Use requests for these specific domains with hardcoded referer
                headers = {
                    "Referer": "https://www.mangago.zone/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(image_url, headers=headers, timeout=30)
            else:
                # Fallback to httpx for other domains
                referer_to_use = chapter_referer # Or parsed_image_url.scheme + "://" + parsed_image_url.netloc + "/"
                response = self.session.get(image_url, headers={"Referer": referer_to_use}, timeout=20)
            response.raise_for_status()
            with open(image_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception:
            return False
    
    def close(self):
        self.session.close()


def _replace_page_number_manhwa(url: str, page_number: int) -> str:
    """
    Replace the page number in a manhwa URL.
    
    Args:
        url (str): The original manhwa URL
        page_number (int): The new page number
        
    Returns:
        str: The URL with the updated page number
    """
    import re
    # Replace pg-X with pg-page_number
    return re.sub(r'pg-\d+', f'pg-{page_number}', url)

def extract_chapter_id(url):
    match = re.search(r"chapter/\d+/(\d+)/", url)
    if match:
        return match.group(1)
    return None

def fetch_chapter_image_urls(chapter_url: str) -> List[str]:
    """
    Extract all image URLs from a paginated chapter.
    Supports various URL formats and uses Selenium for specific domains.
    """
    if not chapter_url:
        raise ParsingError("Chapter URL is invalid.")

    parsed_url = urlparse(chapter_url)
    domain = parsed_url.netloc

    img_urls = []

    if domain in ["www.youhim.me", "www.mangago.zone"]:
        driver = None
        try:
            driver = init_driver()
            current_url = chapter_url
            subpage_idx = 1 # Not strictly needed for img_urls, but good for debugging

            while True:
                driver.get(current_url)

                # Ensure page ready
                wait_first_image(driver, timeout=25)

                # Scroll until all lazy images are in DOM
                imgs = load_all_images_on_subpage(driver, initial_wait=10, pause=1.2, max_rounds=500, stable_rounds=3)

                # Add images from current subpage to list
                for img in sorted(imgs, key=sort_key_by_page_id):
                    src = img.get_attribute("src") or img.get_attribute("data-src")
                    if src:
                        img_urls.append(src)
                
                # Navigate to next subpage (if exists)
                try:
                    next_el = driver.find_element(By.CSS_SELECTOR, "a.next_page")
                    href = next_el.get_attribute("href")
                    if not href:
                        href = next_el.get_attribute("href") or next_el.get_attribute("data-href")
                    if not href:
                        print("✅ No next link visible. Finished chapter subpages.")
                        break

                    current_chapter_id = extract_chapter_id(driver.current_url)
                    next_url = urljoin(driver.current_url, href)
                    next_chapter_id = extract_chapter_id(next_url)

                    if current_chapter_id and next_chapter_id and current_chapter_id != next_chapter_id:
                        print(f"🛑 Next page is a new chapter ({next_chapter_id}). Stopping image collection for current chapter.")
                        break

                    print(f"➡️ Navigating to next subpage: {next_url}")
                    current_url = next_url # Update current_url for next iteration
                    subpage_idx += 1
                    
                    # Apply 10-sec delay and scroll to bottom, then reset to top
                    print("Waiting 10 seconds and scrolling to bottom of new page...")
                    time.sleep(10)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    driver.execute_script("window.scrollTo(0, 0);")

                except NoSuchElementException:
                    print("✅ No more next subpages. Finished chapter.")
                    break
                except TimeoutException:
                    print("⚠️ Timeout while moving to next subpage; stopping image collection.")
                    break
                except Exception as e:
                    print(f"❌ An error occurred during subpage navigation: {e}")
                    break # Break on unexpected errors

            return img_urls
        finally:
            if driver:
                driver.quit()
    else:
        # Existing logic for other domains
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
        options.page_load_strategy = "eager"
        options.add_argument("--ignore-ssl-errors=true")
        options.add_argument("--ignore-certificate-errors")
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(10)

        try:
            driver.get(chapter_url)
            
            # Check if this is a vertical longstrip manhwa URL (pattern: /chapter/id1/id2/)
            is_vertical_longstrip = "/chapter/" in chapter_url and len(chapter_url.split("/")) >= 6
            
            if is_vertical_longstrip:
                # For vertical longstrip manhwa, fetch all images on the single page
                # Wait 10 seconds for the page to load
                time.sleep(10)
                
                # Scroll all the way to the bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait a bit more for any remaining images to load
                time.sleep(2)
                
                # Find image elements with specific patterns (e.g., id="page1", class="page1")
                # Try multiple selectors to catch different patterns
                selectors = [
                    "img[id^='page']",
                    "img[class^='page']",
                    "img[src*='mangapicgallery.com']"
                ]
                
                found_images = set()  # Use set to avoid duplicates
                for selector in selectors:
                    try:
                        img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in img_elements:
                            img_url = img.get_attribute("src")
                            if img_url and img_url not in found_images:
                                # Filter for actual content images
                                # Exclude UI elements like keyboard arrows
                                alt_text = img.get_attribute("alt") or ""
                                if (img_url.endswith(('.jpg', '.jpeg', '.png', '.webp')) and
                                    "arrow" not in alt_text.lower() and
                                    "icon" not in alt_text.lower() and
                                    "button" not in alt_text.lower()):
                                    img_urls.append(img_url)
                                    found_images.add(img_url)
                    except Exception:
                        # Continue with next selector if one fails
                        continue
            else: # For www.mangago.me (non-vertical longstrip)
                # Determine the type of pagination
                is_manhwa = "youhim" in chapter_url or "mangazone" in chapter_url
                is_manga_mangago = "mangago" in chapter_url
                
                # Handling for manhwa URLs (youhim, mangago.zone)
                if is_manhwa:
                    # This part remains unchanged, assuming it works as intended.
                    # If issues arise, they should be addressed separately.
                    pass

                # Handling for manga URLs on mangago.me
                if is_manga_mangago:
                    is_manhwa_uu_url = "/uu/" in chapter_url and "pg-" in chapter_url
                    is_manhwa_mh_url = "/mh/" in chapter_url and "/c" in chapter_url

                    if is_manhwa_uu_url or is_manhwa_mh_url:
                        page_num = 1
                        base_url = chapter_url

                        # Determine the base URL and starting page number
                        if is_manhwa_uu_url:
                            match = re.search(r"(.*/pg-)\d+", chapter_url)
                            if match:
                                base_url = match.group(1)
                            pg_match = re.search(r"pg-(\d+)", chapter_url)
                            if pg_match:
                                page_num = int(pg_match.group(1))
                        elif is_manhwa_mh_url:
                            # For /mh/ URLs, the base is up to the chapter
                            match = re.search(r"(.*/c\d+/)", chapter_url)
                            if match:
                                base_url = match.group(1)
                            pg_match = re.search(r"/c\d+/(\d+)", chapter_url)
                            if pg_match:
                                page_num = int(pg_match.group(1))

                        while True:
                            current_url = ""
                            # Construct the URL for the current page
                            if is_manhwa_uu_url:
                                current_url = f"{base_url}{page_num}/"
                            elif is_manhwa_mh_url:
                                if page_num == 1 and not re.search(r"/c\d+/\d+", base_url):
                                     current_url = base_url
                                else:
                                     current_url = f"{base_url}{page_num}/"

                            if not current_url:
                                break

                            try:
                                if driver.current_url != current_url:
                                    driver.get(current_url)

                                img_selector = f"img#page{page_num}, img.page{page_num}"
                                img = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, img_selector))
                                )
                                img_url = img.get_attribute("src")
                                if img_url:
                                    img_urls.append(img_url)

                                page_num += 1

                            except TimeoutException:
                                print(f"No more pages or image not found for {current_url}.")
                                break
                            except Exception as e:
                                print(f"Error on page {page_num} of {chapter_url}: {e}")
                                break
                else:
                    # Original logic for other regular manga/manhwa (non-mh/uu/cXXX)
                    # This implies it uses .multi_pg_tip.left for total_pages
                    # and appends /i/
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
    Automatically clicks 'show all chapters' button if present.
    Handles different domains.
    """
    parsed_url = urlparse(driver.current_url)
    domain = parsed_url.netloc
    
    chapters = []
    
    if domain in ["www.youhim.me", "www.mangago.zone"]:
        # For these domains, assume a simpler structure for chapter links.
        # This is a generic approach; might need refinement based on actual HTML.
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for common chapter link patterns
        # Example: <a> tags within a div or ul that might contain "chapter" in their href
        chapter_links = soup.find_all('a', href=re.compile(r'/chapter/\d+/\d+/'))
        
        for link in chapter_links:
            title = link.get_text(strip=True)
            url = link.get('href')

            if url and not url.startswith('http'):
                url = urljoin(driver.current_url, url)

            # Try to extract chapter number from title or URL
            number = 0
            match_title = re.search(r'Chapter\s*(\d+(\.\d+)?)', title, re.IGNORECASE)
            match_url = re.search(r'/chapter/\d+/(\d+)/', url)

            if match_title:
                number = float(match_title.group(1))
            elif match_url:
                number = float(match_url.group(1))
            
            if url and title:
                chapters.append(Chapter(number=int(number), title=title, url=url))
        
    else:
        # Existing logic for other domains (e.g., mangago.me)
        try:
            # Look for the "show all chapters" button
            show_all_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@onclick, 'showAllChapters()')]"))
            )
            # Click the button to show all chapters
            show_all_button.click()
            # Wait a bit for the page to update
            time.sleep(2)
        except TimeoutException:
            # No "show all chapters" button found, proceed with existing chapters
            pass
        except Exception as e:
            # Some other error occurred, but we'll continue anyway
            pass
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        chapter_table = soup.find('table', class_='listing')
        if not isinstance(chapter_table, Tag):
            raise DownloadError("Could not find chapter table.")
        
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

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--non-headless=new")
    options.page_load_strategy = "eager"
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    # Make viewport tall-ish so fewer scrolls are needed
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1280, 2200)
    return driver

def wait_first_image(driver, timeout=20):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "img[id^='page']"))
    )

def load_all_images_on_subpage(driver, initial_wait=10, pause=1.0, max_rounds=400, stable_rounds=3):
    """
    Scrolls in steps until the number of images stops increasing for `stable_rounds`.
    This reliably triggers lazy-loading on long vertical strips.
    """
    # start at top
    driver.execute_script("window.scrollTo(0, 0);")
    # give scripts time to inject all <img> tags
    time.sleep(initial_wait)

    prev_count = 0
    stable = 0

    for _ in range(max_rounds):
        # Current images
        imgs = driver.find_elements(By.CSS_SELECTOR, "img[id^='page']")
        count = len(imgs)

        # If new images appeared, reset stability
        if count > prev_count:
            stable = 0
            prev_count = count
        else:
            stable += 1

        # Scroll: bring the last image fully into view; then advance by a viewport
        if imgs:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", imgs[-1])
            except Exception:
                pass

        driver.execute_script("""
            const step = Math.max(window.innerHeight, 900);
            window.scrollBy(0, step);
        """)

        time.sleep(pause)

        # If we've seen no growth for a while, try one hard jump to bottom once
        if stable == stable_rounds - 1:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)

        if stable >= stable_rounds:
            break

    # Final collect
    imgs = driver.find_elements(By.CSS_SELECTOR, "img[id^='page']")
    return imgs

def sort_key_by_page_id(img_el):
    # Extract number from id="page123"
    try:
        pid = img_el.get_attribute("id") or ""
        match = re.search(r"page(\d+)", pid)
        if match:
            n = int(match.group(1))
            return n
        else:
            return 1_000_000 # fallback to push unknowns to end
    except Exception:
        return 1_000_000  # fallback to push unknowns to end
