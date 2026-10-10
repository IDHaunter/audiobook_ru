import json
import tempfile
import unittest
from pathlib import Path

from audiobook_ru.text.chapters import split_book
from audiobook_ru.prepare import prepare_book


class ChapterParsingTests(unittest.TestCase):
    def test_markdown_title_and_numbered_chapters(self):
        source = """## Последний враг человечества

## 1. Утопия
Лето 2037-го выдалось тёплым.

## 2. Подарок
Он открыл дверь.
"""
        front, chapters = split_book(source)
        self.assertEqual(front, "## Последний враг человечества")
        self.assertEqual([c[1] for c in chapters], ["1. Утопия", "2. Подарок"])
        self.assertIn("Лето 2037-го", chapters[0][2])
        self.assertNotIn("Он открыл", chapters[0][2])

    def test_prepare_assigns_distinct_chapter_content_and_rebuilds_manifest(self):
        source = """## Последний враг человечества

## 1. Утопия
Первый текст.

## 2. Подарок
Второй текст.
"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_file = root / "book.md"
            work = root / "work"
            input_file.write_text(source, encoding="utf-8")
            result = prepare_book(str(input_file), str(work), max_chars=100)
            manifest = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(result["chapters"], 2)
            self.assertEqual(len(manifest["chapters"]), 2)
            first_id = manifest["chapters"][0]["segment_ids"][0]
            second_id = manifest["chapters"][1]["segment_ids"][0]
            first_text = (work / "segments" / f"{first_id}.txt").read_text(encoding="utf-8")
            second_text = (work / "segments" / f"{second_id}.txt").read_text(encoding="utf-8")
            self.assertIn("Первый текст", first_text)
            self.assertNotIn("Второй текст", first_text)
            self.assertIn("Второй текст", second_text)
            self.assertNotIn("Первый текст", second_text)


if __name__ == "__main__":
    unittest.main()
