"""Unit tests for src/converter.py."""
import os
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.converter import (
    _get_image_files,
    convert_manga_chapters,
    convert_to_cbz,
    convert_to_pdf,
)


def _create_test_image(path: Path, color: tuple = (255, 0, 0)) -> None:
    """Create a small valid RGB JPEG/PNG image on disk."""
    img = Image.new("RGB", (20, 20), color=color)
    img.save(path)


class TestConverter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _populate_chapter_dir(self, name: str, filenames: list[str]) -> Path:
        ch_dir = self.root / name
        ch_dir.mkdir(parents=True, exist_ok=True)
        for idx, fname in enumerate(filenames):
            _create_test_image(ch_dir / fname, color=(idx * 20 % 256, 50, 100))
        return ch_dir

    def test_numeric_image_sorting_in_get_image_files(self):
        ch_dir = self._populate_chapter_dir(
            "ch_sort", ["10.jpg", "2.jpg", "1.jpg", "11.jpg", "3.jpg", "cover.jpg"]
        )
        files = _get_image_files(str(ch_dir))
        basenames = [os.path.basename(f) for f in files]
        self.assertEqual(
            basenames,
            ["1.jpg", "2.jpg", "3.jpg", "10.jpg", "11.jpg", "cover.jpg"],
        )

    def test_convert_to_cbz_preserves_numeric_order(self):
        ch_dir = self._populate_chapter_dir("Chapter_1", ["10.jpg", "2.jpg", "1.jpg"])
        cbz_path = convert_to_cbz(str(ch_dir), delete_images=False)
        self.assertIsNotNone(cbz_path)
        self.assertTrue(os.path.exists(cbz_path))
        with zipfile.ZipFile(cbz_path, "r") as zf:
            self.assertEqual(zf.namelist(), ["1.jpg", "2.jpg", "10.jpg"])

    def test_convert_to_pdf_preserves_numeric_order_and_closes_handles(self):
        ch_dir = self._populate_chapter_dir("Chapter_2", ["10.jpg", "2.jpg", "1.jpg"])

        captured_args = []
        import img2pdf

        real_convert = img2pdf.convert

        def spy_convert(arg, *args, **kwargs):
            captured_args.append(list(arg))
            return real_convert(arg, *args, **kwargs)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            with patch("src.converter.img2pdf.convert", side_effect=spy_convert):
                pdf_path = convert_to_pdf(str(ch_dir), delete_images=True)

        self.assertIsNotNone(pdf_path)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertEqual(len(captured_args), 1)
        self.assertEqual(
            [os.path.basename(p) for p in captured_args[0]],
            ["1.jpg", "2.jpg", "10.jpg"],
        )
        # Ensure no ResourceWarning (leaked open file handles) was emitted
        resource_warnings = [
            w for w in caught if issubclass(w.category, ResourceWarning)
        ]
        self.assertEqual(resource_warnings, [])
        # Images should be deleted cleanly (would fail on Windows if handles leaked)
        self.assertFalse((ch_dir / "1.jpg").exists())
        self.assertFalse((ch_dir / "2.jpg").exists())
        self.assertFalse((ch_dir / "10.jpg").exists())

    def test_scoped_conversion_only_converts_and_deletes_selected_chapters(self):
        ch1 = self._populate_chapter_dir("Chapter_1", ["1.jpg", "2.jpg"])
        ch2 = self._populate_chapter_dir("Chapter_2", ["1.jpg", "2.jpg"])
        ch3 = self._populate_chapter_dir("Chapter_3", ["1.jpg", "2.jpg"])

        created = convert_manga_chapters(
            str(self.root),
            format="cbz",
            delete_images=True,
            chapter_dirs=[str(ch2)],
        )

        self.assertEqual(len(created), 1)
        self.assertTrue((ch2 / "Chapter_2.cbz").exists())
        # ch2 images deleted
        self.assertFalse((ch2 / "1.jpg").exists())
        self.assertFalse((ch2 / "2.jpg").exists())

        # ch1 and ch3 untouched (no cbz created, images intact)
        self.assertFalse((ch1 / "Chapter_1.cbz").exists())
        self.assertTrue((ch1 / "1.jpg").exists())
        self.assertTrue((ch1 / "2.jpg").exists())

        self.assertFalse((ch3 / "Chapter_3.cbz").exists())
        self.assertTrue((ch3 / "1.jpg").exists())
        self.assertTrue((ch3 / "2.jpg").exists())

    def test_convert_manga_chapters_default_converts_all(self):
        ch1 = self._populate_chapter_dir("Chapter_1", ["1.jpg"])
        ch2 = self._populate_chapter_dir("Chapter_2", ["1.jpg"])

        created = convert_manga_chapters(
            str(self.root), format="pdf", delete_images=False
        )
        self.assertEqual(len(created), 2)
        self.assertTrue((ch1 / "Chapter_1.pdf").exists())
        self.assertTrue((ch2 / "Chapter_2.pdf").exists())

    def test_convert_manga_chapters_empty_list_converts_nothing(self):
        ch1 = self._populate_chapter_dir("Chapter_1", ["1.jpg"])
        created = convert_manga_chapters(
            str(self.root), format="pdf", delete_images=True, chapter_dirs=[]
        )
        self.assertEqual(created, [])
        self.assertFalse((ch1 / "Chapter_1.pdf").exists())
        self.assertTrue((ch1 / "1.jpg").exists())


if __name__ == "__main__":
    unittest.main()
