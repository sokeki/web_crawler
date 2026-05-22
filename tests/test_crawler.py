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


# ---------------------------------------------------------------------------
# Integration tests for the full crawl() BFS loop
# ---------------------------------------------------------------------------

HOME_HTML = """
<html><body>
  <a href="/page2">Page 2</a>
  <a href="/page3">Page 3</a>
</body></html>
"""
PAGE2_HTML = """<html><body><a href="/">Home</a><p>Page two.</p></body></html>"""
PAGE3_HTML = """<html><body><a href="/">Home</a><p>Page three.</p></body></html>"""


def make_session_get(url_map):
    def side_effect(url, **kwargs):
        text = url_map.get(url, "<html></html>")
        return make_response(text)

    return side_effect


class TestCrawlerCrawl(unittest.TestCase):

    @patch("crawler.time.sleep")
    def test_crawls_all_linked_pages(self, mock_sleep):
        url_map = {
            "https://example.com": HOME_HTML,
            "https://example.com/page2": PAGE2_HTML,
            "https://example.com/page3": PAGE3_HTML,
        }
        crawler = Crawler("https://example.com", politeness_window=0)
        with patch.object(
            crawler._session, "get", side_effect=make_session_get(url_map)
        ):
            pages = crawler.crawl()
        self.assertEqual(len(pages), 3)
        self.assertIn("https://example.com", pages)
        self.assertIn("https://example.com/page2", pages)
        self.assertIn("https://example.com/page3", pages)

    @patch("crawler.time.sleep")
    def test_does_not_revisit_pages(self, mock_sleep):
        url_map = {
            "https://example.com": HOME_HTML,
            "https://example.com/page2": PAGE2_HTML,
            "https://example.com/page3": PAGE3_HTML,
        }
        crawler = Crawler("https://example.com", politeness_window=0)
        with patch.object(
            crawler._session, "get", side_effect=make_session_get(url_map)
        ) as mock_get:
            crawler.crawl()
        urls_fetched = [call.args[0] for call in mock_get.call_args_list]
        self.assertEqual(len(urls_fetched), len(set(urls_fetched)))

    @patch("crawler.time.sleep")
    def test_respects_politeness_window(self, mock_sleep):
        url_map = {
            "https://example.com": HOME_HTML,
            "https://example.com/page2": PAGE2_HTML,
        }
        crawler = Crawler("https://example.com", politeness_window=6)
        with patch.object(
            crawler._session, "get", side_effect=make_session_get(url_map)
        ):
            crawler.crawl()
        mock_sleep.assert_called_with(6)

    @patch("crawler.time.sleep")
    def test_skips_failed_pages_and_continues(self, mock_sleep):
        def side_effect(url, **kwargs):
            if "page2" in url:
                resp = make_response("", 404)
                resp.raise_for_status.side_effect = __import__(
                    "requests"
                ).exceptions.HTTPError("404")
                return resp
            return make_response(
                {
                    "https://example.com": HOME_HTML,
                    "https://example.com/page3": PAGE3_HTML,
                }.get(url, "<html></html>")
            )

        crawler = Crawler("https://example.com", politeness_window=0)
        with patch.object(crawler._session, "get", side_effect=side_effect):
            pages = crawler.crawl()
        self.assertNotIn("https://example.com/page2", pages)
        self.assertIn("https://example.com/page3", pages)


if __name__ == "__main__":
    unittest.main()
