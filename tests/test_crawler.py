"""
test_crawler.py - Unit tests for Crawler helpers.

Written before the full crawl() loop so we can verify the building
blocks independently.
"""

import unittest
from unittest.mock import MagicMock, patch

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import Crawler


def make_response(text, status_code=200):
    mock_resp = MagicMock()
    mock_resp.text = text
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class TestCrawlerNormalise(unittest.TestCase):

    def setUp(self):
        self.crawler = Crawler("https://example.com", politeness_window=0)

    def test_strips_fragment(self):
        self.assertEqual(
            self.crawler._normalise("https://example.com/page#section"),
            "https://example.com/page",
        )

    def test_strips_trailing_slash(self):
        self.assertEqual(
            self.crawler._normalise("https://example.com/page/"),
            "https://example.com/page",
        )

    def test_leaves_clean_url_unchanged(self):
        url = "https://example.com/page"
        self.assertEqual(self.crawler._normalise(url), url)


class TestCrawlerExtractLinks(unittest.TestCase):

    def setUp(self):
        self.crawler = Crawler("https://example.com", politeness_window=0)

    def test_extracts_relative_links(self):
        html = '<html><body><a href="/about">About</a></body></html>'
        links = self.crawler._extract_links(html, "https://example.com")
        self.assertIn("https://example.com/about", links)

    def test_ignores_external_links(self):
        html = '<html><body><a href="https://other.com/page">Other</a></body></html>'
        self.assertEqual(self.crawler._extract_links(html, "https://example.com"), [])

    def test_ignores_mailto_links(self):
        html = '<html><body><a href="mailto:test@example.com">Email</a></body></html>'
        self.assertEqual(self.crawler._extract_links(html, "https://example.com"), [])

    def test_converts_relative_to_absolute(self):
        html = '<html><body><a href="page2">Page 2</a></body></html>'
        links = self.crawler._extract_links(html, "https://example.com/")
        self.assertTrue(all(l.startswith("https://example.com") for l in links))


class TestCrawlerFetch(unittest.TestCase):

    def setUp(self):
        self.crawler = Crawler("https://example.com", politeness_window=0)

    @patch("crawler.requests.Session.get")
    def test_returns_html_on_success(self, mock_get):
        mock_get.return_value = make_response("<html></html>")
        self.assertEqual(self.crawler._fetch("https://example.com"), "<html></html>")

    @patch("crawler.requests.Session.get")
    def test_returns_none_on_connection_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("fail")
        self.assertIsNone(self.crawler._fetch("https://example.com"))

    @patch("crawler.requests.Session.get")
    def test_returns_none_on_timeout(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()
        self.assertIsNone(self.crawler._fetch("https://example.com"))

    @patch("crawler.requests.Session.get")
    def test_returns_none_on_http_error(self, mock_get):
        import requests

        mock_resp = make_response("", status_code=404)
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_resp
        self.assertIsNone(self.crawler._fetch("https://example.com/notfound"))


if __name__ == "__main__":
    unittest.main()
