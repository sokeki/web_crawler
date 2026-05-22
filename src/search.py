"""
search.py - Query processing for the search engine.

Provides print and find operations against an inverted index.
"""

import logging

logger = logging.getLogger(__name__)


class Searcher:
    """
    Executes print and find queries against an inverted index.

    Args:
        index: The inverted index produced by Indexer (word -> url -> stats).
    """

    def __init__(self, index: dict):
        self.index = index

    def print_word(self, word: str) -> str:
        """
        Return a formatted string showing all index entries for a word.

        Args:
            word: The word to look up (case-insensitive).

        Returns:
            Human-readable string with per-page frequency and positions,
            or a not found message.
        """
        word = word.lower().strip()

        if not word:
            return "Error: no word provided."

        if word not in self.index:
            return f'Word "{word}" not found in the index.'

        entries = self.index[word]
        lines = [f'Index entries for "{word}" ({len(entries)} page(s)):\n']

        for url, stats in sorted(entries.items()):
            freq = stats.get("frequency", 0)
            positions = stats.get("positions", [])
            lines.append(f"  {url}")
            lines.append(f"    frequency : {freq}")
            lines.append(f"    positions : {positions}\n")

        return "\n".join(lines)

    def find(self, query: str) -> str:
        """
        Find pages containing ALL words in the query (AND search).

        Args:
            query: One or more space-separated search terms (case-insensitive).

        Returns:
            Human-readable string listing matching pages, or a message if
            no pages match.
        """
        query = query.strip()

        if not query:
            return "Error: empty query."

        terms = [t.lower() for t in query.split()]

        url_sets = []
        missing_terms = []
        for term in terms:
            if term in self.index:
                url_sets.append(set(self.index[term].keys()))
            else:
                missing_terms.append(term)

        if missing_terms:
            missing_str = ", ".join(f'"{t}"' for t in missing_terms)
            return f"No pages found. The following term(s) are not in the index: {missing_str}."

        matching_urls = url_sets[0]
        for s in url_sets[1:]:
            matching_urls = matching_urls & s

        if not matching_urls:
            terms_str = " ".join(f'"{t}"' for t in terms)
            return f"No pages contain all of the terms: {terms_str}."

        lines = [
            f'Pages containing {" + ".join(f"{chr(34)}{t}{chr(34)}" for t in terms)} ({len(matching_urls)} result(s)):\n'
        ]
        for url in sorted(matching_urls):
            freq_info = "  |  ".join(
                f'"{t}": {self.index[t][url]["frequency"]}x' for t in terms
            )
            lines.append(f"  {url}  [{freq_info}]")

        return "\n".join(lines)
