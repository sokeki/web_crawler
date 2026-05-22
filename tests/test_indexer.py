"""
test_indexer.py - Unit tests for the Indexer class.
"""

import json
import os
import tempfile
import unittest

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from indexer import Indexer

SIMPLE_HTML = """
<html><body>
  <p>The quick brown fox jumps over the lazy dog.</p>
</body></html>
"""

MULTI_PAGE_HTML_1 = """
<html><body><p>hello world hello</p></body></html>
"""

MULTI_PAGE_HTML_2 = """
<html><body><p>world is beautiful hello world</p></body></html>
"""

MIXED_CASE_HTML = """
<html><body><p>Hello HELLO hElLo</p></body></html>
"""

SCRIPT_HTML = """
<html>
  <head><script>var x = "ignore this";</script></head>
  <body><p>visible text</p></body>
</html>
"""


class TestIndexerExtractWords(unittest.TestCase):

    def setUp(self):
        self.indexer = Indexer()

    def test_basic_tokenisation(self):
        words = self.indexer._extract_words(SIMPLE_HTML)
        self.assertIn("quick", words)
        self.assertIn("fox", words)
        self.assertIn("dog", words)

    def test_lowercase_output(self):
        words = self.indexer._extract_words(MIXED_CASE_HTML)
        for w in words:
            self.assertEqual(w, w.lower())

    def test_strips_script_tags(self):
        words = self.indexer._extract_words(SCRIPT_HTML)
        self.assertNotIn("ignore", words)
        self.assertIn("visible", words)
        self.assertIn("text", words)

    def test_empty_html(self):
        words = self.indexer._extract_words("<html></html>")
        self.assertEqual(words, [])

    def test_numbers_excluded(self):
        html = "<html><body><p>there are 42 reasons</p></body></html>"
        words = self.indexer._extract_words(html)
        self.assertNotIn("42", words)
        self.assertIn("there", words)
        self.assertIn("reasons", words)


class TestIndexerBuild(unittest.TestCase):

    def setUp(self):
        self.indexer = Indexer()

    def test_single_page_frequency(self):
        pages = {"http://example.com": MULTI_PAGE_HTML_1}
        self.indexer.build(pages)
        self.assertIn("hello", self.indexer.index)
        self.assertEqual(
            self.indexer.index["hello"]["http://example.com"]["frequency"], 2
        )

    def test_single_page_positions(self):
        pages = {"http://example.com": MULTI_PAGE_HTML_1}
        self.indexer.build(pages)
        positions = self.indexer.index["hello"]["http://example.com"]["positions"]
        self.assertEqual(len(positions), 2)

    def test_multi_page_index(self):
        pages = {
            "http://example.com/1": MULTI_PAGE_HTML_1,
            "http://example.com/2": MULTI_PAGE_HTML_2,
        }
        self.indexer.build(pages)
        self.assertIn("http://example.com/1", self.indexer.index["world"])
        self.assertIn("http://example.com/2", self.indexer.index["world"])

    def test_case_insensitive_indexing(self):
        pages = {"http://example.com": MIXED_CASE_HTML}
        self.indexer.build(pages)
        self.assertEqual(
            self.indexer.index["hello"]["http://example.com"]["frequency"], 3
        )

    def test_empty_pages(self):
        self.indexer.build({})
        self.assertEqual(len(self.indexer.index), 0)

    def test_rebuild_replaces_old_index(self):
        pages1 = {"http://example.com": "<html><body>first build</body></html>"}
        pages2 = {"http://example.com": "<html><body>second rebuild</body></html>"}
        self.indexer.build(pages1)
        self.assertIn("first", self.indexer.index)
        self.indexer.build(pages2)
        self.assertNotIn("first", self.indexer.index)
        self.assertIn("second", self.indexer.index)


class TestIndexerSaveLoad(unittest.TestCase):

    def setUp(self):
        self.indexer = Indexer()
        pages = {
            "http://example.com/1": MULTI_PAGE_HTML_1,
            "http://example.com/2": MULTI_PAGE_HTML_2,
        }
        self.indexer.build(pages)

    def test_save_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            self.indexer.save(path)
            self.assertTrue(os.path.exists(path))
        finally:
            os.unlink(path)

    def test_save_produces_valid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            self.indexer.save(path)
            with open(path) as f:
                data = json.load(f)
            self.assertIsInstance(data, dict)
        finally:
            os.unlink(path)

    def test_load_restores_index(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            self.indexer.save(path)
            new_indexer = Indexer()
            new_indexer.load(path)
            self.assertEqual(new_indexer.index["hello"], self.indexer.index["hello"])
        finally:
            os.unlink(path)

    def test_load_missing_file_raises(self):
        new_indexer = Indexer()
        with self.assertRaises(FileNotFoundError):
            new_indexer.load("/nonexistent/path/index.json")


if __name__ == "__main__":
    unittest.main()
