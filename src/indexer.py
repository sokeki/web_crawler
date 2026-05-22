"""
indexer.py - Inverted index builder for the search engine.

Parses HTML pages produced by the crawler and constructs an inverted
index that stores, for each word, a mapping of URL -> {frequency, positions}.
"""

import json
import re
import logging
from collections import defaultdict

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Indexer:
    """
    Builds and persists an inverted index from crawled HTML pages.

    Index structure:
        {
          "word": {
            "url1": {"frequency": 3, "positions": [5, 12, 34]},
            "url2": {"frequency": 1, "positions": [7]}
          }
        }

    The index is case-insensitive (all words are lowercased).
    """

    def __init__(self):
        self.index: dict[str, dict[str, dict]] = defaultdict(dict)

    def build(self, pages: dict[str, str]) -> None:
        """
        Build the inverted index from a dict of {url: html}.

        Args:
            pages: Mapping of URL -> raw HTML content.
        """
        self.index = defaultdict(dict)

        for url, html in pages.items():
            words = self._extract_words(html)
            self._index_page(url, words)
            logger.info("Indexed %s  (%d tokens)", url, len(words))

        logger.info(
            "Index built: %d unique words across %d pages.", len(self.index), len(pages)
        )

    def save(self, filepath: str) -> None:
        """
        Serialise the index to a JSON file.

        Args:
            filepath: Path where the index file will be written.
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        logger.info("Index saved to %s", filepath)

    def load(self, filepath: str) -> None:
        """
        Load a previously saved index from a JSON file.

        Args:
            filepath: Path to the JSON index file.

        Raises:
            FileNotFoundError: If the index file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            self.index = json.load(f)
        logger.info("Index loaded from %s  (%d words)", filepath, len(self.index))

    def _extract_words(self, html: str) -> list[str]:
        """
        Strip HTML tags and return a list of lowercase word tokens.

        Only alphabetic tokens are kept (numbers and punctuation removed).
        """
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        words = re.findall(r"[a-z]+", text.lower())
        return words

    def _index_page(self, url: str, words: list[str]) -> None:
        """Record word frequencies and positions for a single page."""
        word_data: dict[str, dict] = defaultdict(
            lambda: {"frequency": 0, "positions": []}
        )

        for position, word in enumerate(words):
            word_data[word]["frequency"] += 1
            word_data[word]["positions"].append(position)

        for word, stats in word_data.items():
            self.index[word][url] = stats
