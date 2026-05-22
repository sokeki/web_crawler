"""
crawler.py - Web crawler for the search engine.

Initial implementation: fetch a single page and extract same-domain links.
Politeness window and full BFS loop to follow in next iteration.
"""

import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_POLITENESS = 6


class Crawler:
    def __init__(self, base_url: str, politeness_window: int = DEFAULT_POLITENESS):
        self.base_url = base_url
        self.politeness_window = politeness_window
        self.pages: dict[str, str] = {}
        self._visited: set[str] = set()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "COMP3011-SearchBot/1.0"})

    def _normalise(self, url: str) -> str:
        """Strip fragments and trailing slashes for consistent deduplication."""
        parsed = urlparse(url)
        clean = parsed._replace(fragment="").geturl()
        return clean.rstrip("/")

    def _fetch(self, url: str) -> str | None:
        """Fetch a URL and return its HTML, or None on error."""
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            logger.warning("HTTP error fetching %s: %s", url, e)
        except requests.exceptions.ConnectionError as e:
            logger.warning("Connection error fetching %s: %s", url, e)
        except requests.exceptions.Timeout:
            logger.warning("Timeout fetching %s", url)
        except requests.exceptions.RequestException as e:
            logger.warning("Request error fetching %s: %s", url, e)
        return None

    def _extract_links(self, html: str, current_url: str) -> list[str]:
        """Parse HTML and return same-domain links as absolute URLs."""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        base_domain = urlparse(self.base_url).netloc

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            absolute = urljoin(current_url, href)
            parsed = urlparse(absolute)

            if parsed.scheme in ("http", "https") and parsed.netloc == base_domain:
                clean = self._normalise(absolute)
                links.append(clean)

        return links

    def crawl(self) -> dict[str, str]:
        """
        Crawl all pages reachable from base_url within the same domain.

        Uses a BFS queue so pages are visited in breadth-first order.
        Waits self.politeness_window seconds between successive requests.

        Returns:
            dict mapping URL -> HTML content for every successfully crawled page.
        """
        self.pages = {}
        self._visited = set()
        queue = [self.base_url]

        while queue:
            url = queue.pop(0)
            normalised = self._normalise(url)

            if normalised in self._visited:
                continue
            self._visited.add(normalised)

            html = self._fetch(normalised)
            if html is None:
                continue

            self.pages[normalised] = html
            logger.info("Crawled: %s  (total: %d)", normalised, len(self.pages))

            new_links = self._extract_links(html, normalised)
            for link in new_links:
                if link not in self._visited:
                    queue.append(link)

            if queue:
                logger.info(
                    "Waiting %ds (politeness window)...", self.politeness_window
                )
                time.sleep(self.politeness_window)

        logger.info("Crawl complete. %d pages collected.", len(self.pages))
        return self.pages
