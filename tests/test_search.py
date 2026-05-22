"""
test_search.py - Unit tests for the Searcher class.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from search import Searcher

SAMPLE_INDEX = {
    "hello": {
        "http://example.com/page1": {"frequency": 3, "positions": [0, 5, 10]},
        "http://example.com/page2": {"frequency": 1, "positions": [2]},
    },
    "world": {
        "http://example.com/page1": {"frequency": 1, "positions": [1]},
        "http://example.com/page3": {"frequency": 2, "positions": [0, 4]},
    },
    "indifference": {
        "http://example.com/page3": {"frequency": 1, "positions": [7]},
    },
    "good": {
        "http://example.com/page1": {"frequency": 2, "positions": [3, 8]},
        "http://example.com/page2": {"frequency": 1, "positions": [6]},
    },
    "friends": {
        "http://example.com/page2": {"frequency": 1, "positions": [9]},
    },
}


class TestSearcherPrintWord(unittest.TestCase):

    def setUp(self):
        self.searcher = Searcher(SAMPLE_INDEX)

    def test_known_word_returns_entries(self):
        result = self.searcher.print_word("hello")
        self.assertIn("hello", result)
        self.assertIn("http://example.com/page1", result)
        self.assertIn("http://example.com/page2", result)

    def test_shows_frequency(self):
        result = self.searcher.print_word("hello")
        self.assertIn("3", result)

    def test_shows_positions(self):
        result = self.searcher.print_word("hello")
        self.assertIn("0", result)

    def test_unknown_word_returns_not_found(self):
        result = self.searcher.print_word("nonsense")
        self.assertIn("not found", result.lower())

    def test_case_insensitive(self):
        result_lower = self.searcher.print_word("hello")
        result_upper = self.searcher.print_word("HELLO")
        self.assertEqual(result_lower, result_upper)

    def test_empty_word_returns_error(self):
        result = self.searcher.print_word("")
        self.assertIn("error", result.lower())

    def test_whitespace_only_returns_error(self):
        result = self.searcher.print_word("   ")
        self.assertIn("error", result.lower())


class TestSearcherFind(unittest.TestCase):

    def setUp(self):
        self.searcher = Searcher(SAMPLE_INDEX)

    def test_single_word_finds_all_pages(self):
        result = self.searcher.find("hello")
        self.assertIn("http://example.com/page1", result)
        self.assertIn("http://example.com/page2", result)

    def test_multi_word_intersection(self):
        result = self.searcher.find("good friends")
        self.assertNotIn("page1", result)
        self.assertIn("http://example.com/page2", result)

    def test_no_intersection_returns_no_pages(self):
        result = self.searcher.find("indifference hello")
        self.assertIn("no pages", result.lower())

    def test_unknown_word_reports_missing_term(self):
        result = self.searcher.find("xyzzy")
        self.assertIn("not in the index", result.lower())

    def test_case_insensitive_query(self):
        result_lower = self.searcher.find("hello")
        result_upper = self.searcher.find("HELLO")
        self.assertEqual(result_lower, result_upper)

    def test_empty_query_returns_error(self):
        result = self.searcher.find("")
        self.assertIn("error", result.lower())

    def test_whitespace_query_returns_error(self):
        result = self.searcher.find("   ")
        self.assertIn("error", result.lower())

    def test_result_count_shown(self):
        result = self.searcher.find("hello")
        self.assertIn("2", result)

    def test_single_page_result(self):
        result = self.searcher.find("indifference")
        self.assertIn("http://example.com/page3", result)

    def test_mixed_case_multi_word(self):
        result = self.searcher.find("Good Friends")
        self.assertIn("http://example.com/page2", result)


if __name__ == "__main__":
    unittest.main()
