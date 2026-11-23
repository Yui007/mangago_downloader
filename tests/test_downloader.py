"""Unit tests for src/downloader.py."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from selenium.common.exceptions import TimeoutException

from src.downloader import (
    ChapterDownloader,
    _build_chapter_dir_name,
    _replace_page_number_manhwa,
    fetch_chapter_image_urls,
    get_chapter_list,
    init_driver,
)
from src.models import Chapter, Manga


class TestPaginationURLs(unittest.TestCase):
    def test_replace_page_number_helper(self):
        url = "https://www.mangago.me/read-manga/sample/nml_chapter-396/pg-1/"
        self.assertEqual(
            _replace_page_number_manhwa(url, 6),
            "https://www.mangago.me/read-manga/sample/nml_chapter-396/pg-6/",
        )
        self.assertNotIn("/pg-1/6/", _replace_page_number_manhwa(url, 6))

    def test_fetch_chapter_image_urls_pg_pagination(self):
        start_url = "https://www.mangago.me/read-manga/sample/nml_chapter-396/pg-1/"
        visited_urls = []

        class FakeDriver:
            def __init__(self):
                self.current_url = ""

            def set_page_load_timeout(self, t):
                pass

            def get(self, url):
                visited_urls.append(url)
                self.current_url = url

            def quit(self):
                pass

        fake_driver = FakeDriver()

        # Simulate 6 pages (pg-1 through pg-6), then TimeoutException on pg-7
        page_counter = {"n": 0}

        class FakeWait:
            def __init__(self, driver, timeout):
                self.driver = driver

            def until(self, condition):
                page_counter["n"] += 1
                n = page_counter["n"]
                if n > 6:
                    raise TimeoutException("no more pages")
                img = MagicMock()
                img.get_attribute.return_value = f"https://cdn.example.com/page{n}.jpg"
                return img

        with (
            patch("src.downloader.webdriver.Chrome", return_value=fake_driver),
            patch("src.downloader.WebDriverWait", FakeWait),
        ):
            imgs = fetch_chapter_image_urls(start_url)

        expected_urls = [
            f"https://www.mangago.me/read-manga/sample/nml_chapter-396/pg-{i}/"
            for i in range(1, 8)
        ]
        self.assertEqual(visited_urls, expected_urls)
        self.assertFalse(any("/pg-1/" in u and u != start_url for u in visited_urls))
        self.assertEqual(
            imgs,
            [f"https://cdn.example.com/page{i}.jpg" for i in range(1, 7)],
        )

    def test_fetch_chapter_image_urls_fallback_pattern_preserved(self):
        start_url = "https://www.mangago.me/read-manga/sample/mi/12345/"
        visited_urls = []

        class FakeDriver:
            def __init__(self):
                self.current_url = ""

            def set_page_load_timeout(self, t):
                pass

            def get(self, url):
                visited_urls.append(url)
                self.current_url = url

            def quit(self):
                pass

        fake_driver = FakeDriver()
        wait_calls = {"n": 0}

        class FakeWait:
            def __init__(self, driver, timeout):
                pass

            def until(self, condition):
                wait_calls["n"] += 1
                if wait_calls["n"] == 1:
                    el = MagicMock()
                    el.text = "(1/3)"
                    return el
                img = MagicMock()
                img.get_attribute.return_value = (
                    f"https://cdn.example.com/p{wait_calls['n'] - 1}.jpg"
                )
                return img

        with (
            patch("src.downloader.webdriver.Chrome", return_value=fake_driver),
            patch("src.downloader.WebDriverWait", FakeWait),
        ):
            imgs = fetch_chapter_image_urls(start_url)

        self.assertEqual(
            visited_urls,
            [
                "https://www.mangago.me/read-manga/sample/mi/12345/",
                "https://www.mangago.me/read-manga/sample/mi/12345/2/",
                "https://www.mangago.me/read-manga/sample/mi/12345/3/",
            ],
        )
        self.assertEqual(len(imgs), 3)


class TestChapterListOrdering(unittest.TestCase):
    def test_get_chapter_list_preserves_site_order_with_specials_and_decimals(self):
        # Mangago chapter table is newest-first
        html = """
        <html><body>
        <table class="listing">
            <tr><td><a class="chico" href="/read-manga/test/c6/">Side Story 1</a></td></tr>
            <tr><td><a class="chico" href="/read-manga/test/c5/">Ch. 3</a></td></tr>
            <tr><td><a class="chico" href="/read-manga/test/c4/">Ch. 2.5</a></td></tr>
            <tr><td><a class="chico" href="/read-manga/test/c3/">Vol. 2 Special</a></td></tr>
            <tr><td><a class="chico" href="/read-manga/test/c2/">Ch. 2</a></td></tr>
            <tr><td><a class="chico" href="/read-manga/test/c1/">Special.</a></td></tr>
            <tr><td><a class="chico" href="/read-manga/test/c0/">Ch. 1</a></td></tr>
        </table>
        </body></html>
        """
        driver = MagicMock()
        driver.current_url = "https://www.mangago.me/read-manga/test/"
        driver.page_source = html

        with patch("src.downloader.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException("no button")
            chapters = get_chapter_list(driver)

        titles = [ch.title for ch in chapters]
        # Must be oldest-first (exact reverse of table), NOT re-sorted by parsed number
        self.assertEqual(
            titles,
            [
                "Ch. 1",
                "Special.",
                "Ch. 2",
                "Vol. 2 Special",
                "Ch. 2.5",
                "Ch. 3",
                "Side Story 1",
            ],
        )

    def test_duplicate_parsed_chapter_numbers_do_not_collide_on_disk(self):
        manga = Manga(title="Collision Test", url="https://www.mangago.me/read-manga/test/")
        ch_main = Chapter(
            number=1,
            title="Ch. 1",
            url="https://www.mangago.me/read-manga/test/ch-1/pg-1/",
            image_urls=["https://cdn.example.com/a.jpg"],
        )
        ch_side = Chapter(
            number=1,
            title="Side Story 1",
            url="https://www.mangago.me/read-manga/test/side-1/pg-1/",
            image_urls=["https://cdn.example.com/b.jpg"],
        )
        ch_same_title = Chapter(
            number=1,
            title="Ch. 1",
            url="https://www.mangago.me/read-manga/test/ch-1-alt/pg-1/",
            image_urls=["https://cdn.example.com/c.jpg"],
        )

        names = {
            _build_chapter_dir_name(ch_main),
            _build_chapter_dir_name(ch_side),
            _build_chapter_dir_name(ch_same_title),
        }
        self.assertEqual(len(names), 3)

        with tempfile.TemporaryDirectory() as tmp:
            downloader = ChapterDownloader(download_dir=tmp)
            try:
                def fake_download(url, path, referer):
                    Path(path).write_bytes(url.encode("utf-8"))
                    return True

                with patch.object(downloader, "_download_image", side_effect=fake_download):
                    r1 = downloader.download_chapter(manga, ch_main)
                    r2 = downloader.download_chapter(manga, ch_side)
                    r3 = downloader.download_chapter(manga, ch_same_title)

                self.assertTrue(r1.success and r2.success and r3.success)
                self.assertEqual(len({r1.file_path, r2.file_path, r3.file_path}), 3)
                # Verify each chapter's file was preserved and not overwritten
                self.assertEqual(
                    (Path(r1.file_path) / "001.jpg").read_bytes(),
                    b"https://cdn.example.com/a.jpg",
                )
                self.assertEqual(
                    (Path(r2.file_path) / "001.jpg").read_bytes(),
                    b"https://cdn.example.com/b.jpg",
                )
                self.assertEqual(
                    (Path(r3.file_path) / "001.jpg").read_bytes(),
                    b"https://cdn.example.com/c.jpg",
                )
            finally:
                downloader.close()


class TestChapterDownloadResult(unittest.TestCase):
    def test_download_chapter_returns_false_when_zero_images_download(self):
        manga = Manga(title="Fail Manga", url="https://www.mangago.me/read-manga/fail/")
        chapter = Chapter(
            number=1,
            title="Ch. 1",
            url="https://www.mangago.me/read-manga/fail/c1/",
            image_urls=[
                "https://cdn.example.com/1.jpg",
                "https://cdn.example.com/2.jpg",
            ],
        )

        with tempfile.TemporaryDirectory() as tmp:
            downloader = ChapterDownloader(download_dir=tmp)
            try:
                with patch.object(downloader, "_download_image", return_value=False):
                    result = downloader.download_chapter(manga, chapter)

                self.assertFalse(result.success)
                self.assertEqual(result.images_downloaded, 0)
                self.assertTrue(result.error_message)
            finally:
                downloader.close()

    def test_download_chapter_returns_false_when_no_image_urls(self):
        manga = Manga(title="Empty Manga", url="https://www.mangago.me/read-manga/empty/")
        chapter = Chapter(
            number=1,
            title="Ch. 1",
            url="https://www.mangago.me/read-manga/empty/c1/",
            image_urls=[],
        )

        with tempfile.TemporaryDirectory() as tmp:
            downloader = ChapterDownloader(download_dir=tmp)
            try:
                result = downloader.download_chapter(manga, chapter)
                self.assertFalse(result.success)
                self.assertEqual(result.images_downloaded, 0)
                self.assertTrue(result.error_message)
            finally:
                downloader.close()


class TestInitDriver(unittest.TestCase):
    def test_init_driver_has_no_invalid_non_headless_flag(self):
        captured_options = []

        def fake_chrome(options=None, **kwargs):
            captured_options.append(options)
            return MagicMock()

        with patch("src.downloader.webdriver.Chrome", side_effect=fake_chrome):
            init_driver()

        self.assertEqual(len(captured_options), 1)
        args = captured_options[0].arguments
        self.assertNotIn("--non-headless=new", args)


if __name__ == "__main__":
    unittest.main()
