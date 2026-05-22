"""
main.py - Command-line interface for the COMP3011 Search Engine Tool.

Commands:
    build  - Crawl the target website and build the inverted index.
    load   - Load a previously saved index from disk.
    print  - Print the index entry for a given word.
    find   - Find pages containing one or more search terms.
    help   - Show available commands.
    quit   - Exit the shell.
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

from crawler import Crawler
from indexer import Indexer
from search import Searcher

TARGET_URL = "https://quotes.toscrape.com"
INDEX_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "index.json")
POLITENESS_WINDOW = 6

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

HELP_TEXT = """
Available commands:
  build          Crawl the website and build the inverted index.
  load           Load a previously built index from disk.
  print <word>   Print the inverted index entry for <word>.
  find <query>   Find pages containing all words in <query>.
  help           Show this help message.
  quit / exit    Exit the search tool.

Examples:
  > build
  > load
  > print nonsense
  > find indifference
  > find good friends
"""


def run_shell():
    """Start the interactive command-line shell."""
    indexer = Indexer()
    searcher: Searcher | None = None
    index_loaded = False

    print("COMP3011 Search Engine Tool")
    print('Type "help" for available commands.\n')

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "build":
            print(f"Starting crawl of {TARGET_URL} ...")
            print(
                f"(Politeness window: {POLITENESS_WINDOW}s - this will take a while)\n"
            )
            crawler = Crawler(TARGET_URL, politeness_window=POLITENESS_WINDOW)
            pages = crawler.crawl()

            print(f"\nBuilding index from {len(pages)} pages ...")
            indexer.build(pages)

            os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
            indexer.save(INDEX_FILE)

            searcher = Searcher(indexer.index)
            index_loaded = True
            print(f"Index built and saved to {INDEX_FILE}\n")

        elif command == "load":
            if not os.path.exists(INDEX_FILE):
                print(f'Index file not found at "{INDEX_FILE}". Run "build" first.\n')
                continue
            try:
                indexer.load(INDEX_FILE)
                searcher = Searcher(indexer.index)
                index_loaded = True
                print(f"Index loaded from {INDEX_FILE}  ({len(indexer.index)} words)\n")
            except Exception as e:
                print(f"Error loading index: {e}\n")

        elif command == "print":
            if not index_loaded:
                print('No index loaded. Run "build" or "load" first.\n')
                continue
            if not args:
                print("Usage: print <word>\n")
                continue
            print(searcher.print_word(args))
            print()

        elif command == "find":
            if not index_loaded:
                print('No index loaded. Run "build" or "load" first.\n')
                continue
            if not args:
                print("Usage: find <word> [word2 ...]\n")
                continue
            print(searcher.find(args))
            print()

        elif command in ("help", "?"):
            print(HELP_TEXT)

        elif command in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        else:
            print(
                f'Unknown command: "{command}". Type "help" for available commands.\n'
            )


if __name__ == "__main__":
    run_shell()
