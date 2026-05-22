"""
crawler.py - Web crawler for the search engine.

Initial implementation: fetch a single page and extract same-domain links.
Politeness window and full BFS loop to follow in next iteration.
"""

import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

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
        """Placeholder - full BFS loop not yet implemented."""
        raise NotImplementedError("Not fully developed yet")
