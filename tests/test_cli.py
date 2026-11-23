"""Unit tests for cli/main_cli.py."""
import unittest
from unittest.mock import MagicMock, patch

from cli import main_cli
from src.models import Chapter, DownloadResult, Manga


class _StopCLI(BaseException):
    """Sentinel exception to break out of the CLI main loop in tests."""


class TestMainCLI(unittest.TestCase):
    def _sample_manga_and_chapters(self):
        manga = Manga(title="Test Manga", url="https://www.mangago.me/read-manga/test/")
        chapters = [
            Chapter(number=1.0, url="https://www.mangago.me/read-manga/test/c1/", title="Ch. 1"),
            Chapter(number=2.0, url="https://www.mangago.me/read-manga/test/c2/", title="Ch. 2"),
            Chapter(number=3.0, url="https://www.mangago.me/read-manga/test/c3/", title="Ch. 3"),
        ]
        return manga, chapters

    def test_empty_search_on_page_1_does_not_loop_infinitely(self):
        search_calls = []

        def fake_search(title, page=1):
            search_calls.append((title, page))
            return []

        prompt_answers = iter(["1", "nonexistent manga"])

        def fake_prompt(*args, **kwargs):
            try:
                return next(prompt_answers)
            except StopIteration:
                raise _StopCLI()

        with (
            patch.object(main_cli, "search_manga", side_effect=fake_search),
            patch.object(main_cli.Prompt, "ask", side_effect=fake_prompt),
            patch.object(main_cli.console, "print"),
        ):
            with self.assertRaises(_StopCLI):
                main_cli.main()

        # Must only query page 1 once and break back to the main menu
        self.assertEqual(search_calls, [("nonexistent manga", 1)])

    def test_range_validation_rejects_invalid_ranges(self):
        manga, chapters = self._sample_manga_and_chapters()
        invalid_pairs = [
            (0, 2),      # start == 0
            (-1, 2),     # negative start
            (3, 1),      # start > end
            (1, 4),      # end > len(chapters)
            (4, 5),      # both out of bounds
        ]

        for start, end in invalid_pairs:
            with self.subTest(start=start, end=end):
                # Sequence: choose URL (2), enter URL, choose range (2), then next iteration raises _StopCLI
                prompt_answers = iter(["2", manga.url, "2"])
                int_answers = iter([start, end])

                def fake_prompt(*args, **kwargs):
                    try:
                        return next(prompt_answers)
                    except StopIteration:
                        raise _StopCLI()

                mock_dl_cls = MagicMock()
                printed = []

                with (
                    patch.object(main_cli, "get_manga_details", return_value=(manga, MagicMock())),
                    patch.object(main_cli, "get_chapter_list", return_value=chapters),
                    patch.object(main_cli, "close_driver"),
                    patch.object(main_cli, "ChapterDownloader", mock_dl_cls),
                    patch.object(main_cli.Prompt, "ask", side_effect=fake_prompt),
                    patch.object(main_cli.IntPrompt, "ask", side_effect=lambda *a, **k: next(int_answers)),
                    patch.object(main_cli.console, "print", side_effect=lambda *a, **k: printed.append(" ".join(str(x) for x in a))),
                ):
                    with self.assertRaises(_StopCLI):
                        main_cli.main()

                mock_dl_cls.assert_not_called()
                self.assertTrue(
                    any("Invalid chapter index range" in line for line in printed),
                    f"Expected invalid range message for ({start}, {end}), got: {printed}",
                )

    def test_single_chapter_validation_rejects_invalid_indices(self):
        manga, chapters = self._sample_manga_and_chapters()
        for bad_idx in [0, -2, 4, 99]:
            with self.subTest(chapter_idx=bad_idx):
                prompt_answers = iter(["2", manga.url, "3"])

                def fake_prompt(*args, **kwargs):
                    try:
                        return next(prompt_answers)
                    except StopIteration:
                        raise _StopCLI()

                mock_dl_cls = MagicMock()
                printed = []

                with (
                    patch.object(main_cli, "get_manga_details", return_value=(manga, MagicMock())),
                    patch.object(main_cli, "get_chapter_list", return_value=chapters),
                    patch.object(main_cli, "close_driver"),
                    patch.object(main_cli, "ChapterDownloader", mock_dl_cls),
                    patch.object(main_cli.Prompt, "ask", side_effect=fake_prompt),
                    patch.object(main_cli.IntPrompt, "ask", return_value=bad_idx),
                    patch.object(main_cli.console, "print", side_effect=lambda *a, **k: printed.append(" ".join(str(x) for x in a))),
                ):
                    with self.assertRaises(_StopCLI):
                        main_cli.main()

                mock_dl_cls.assert_not_called()
                self.assertTrue(
                    any("Invalid chapter index" in line for line in printed),
                    f"Expected invalid index message for {bad_idx}, got: {printed}",
                )

    def test_cli_passes_only_successful_downloaded_dirs_to_converter(self):
        manga, chapters = self._sample_manga_and_chapters()
        # Choose URL (2), enter URL, choose range (2), format pdf
        prompt_answers = iter(["2", manga.url, "2", "pdf"])
        # start=1, end=2
        int_answers = iter([1, 2])
        # delete_images=True, download another=False
        confirm_answers = iter([True, False])

        dl_results = [
            DownloadResult(
                chapter=chapters[0],
                success=True,
                file_path="downloads/Test Manga/Chapter_1",
                images_downloaded=5,
            ),
            DownloadResult(
                chapter=chapters[1],
                success=False,
                file_path="downloads/Test Manga/Chapter_2",
                error_message="All images failed",
                images_downloaded=0,
            ),
        ]

        mock_downloader = MagicMock()
        mock_downloader.download_chapters.return_value = dl_results
        mock_convert = MagicMock(return_value=["downloads/Test Manga/Chapter_1/Chapter_1.pdf"])

        with (
            patch.object(main_cli, "get_manga_details", return_value=(manga, MagicMock())),
            patch.object(main_cli, "get_chapter_list", return_value=chapters),
            patch.object(main_cli, "close_driver"),
            patch.object(main_cli, "fetch_chapter_image_urls", return_value=["https://img/1.jpg"]),
            patch.object(main_cli, "ChapterDownloader", return_value=mock_downloader),
            patch.object(main_cli, "convert_manga_chapters", mock_convert),
            patch.object(main_cli.Prompt, "ask", side_effect=lambda *a, **k: next(prompt_answers)),
            patch.object(main_cli.IntPrompt, "ask", side_effect=lambda *a, **k: next(int_answers)),
            patch.object(main_cli.Confirm, "ask", side_effect=lambda *a, **k: next(confirm_answers)),
            patch.object(main_cli.console, "print"),
        ):
            main_cli.main()

        mock_convert.assert_called_once()
        _, kwargs = mock_convert.call_args
        self.assertEqual(kwargs.get("chapter_dirs"), ["downloads/Test Manga/Chapter_1"])


if __name__ == "__main__":
    unittest.main()
