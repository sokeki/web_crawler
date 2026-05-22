# COMP3011 Search Engine Tool

A command-line search engine built for the COMP3011 Web Services and Web Data module.

## Overview

This tool crawls [quotes.toscrape.com](https://quotes.toscrape.com), builds an inverted
index of all words found across the site, and lets you query it interactively.

## Planned Commands

- `build` - crawl the website and build the index
- `load` - load a previously built index from disk
- `print <word>` - show index entries for a word
- `find <query>` - find pages containing search terms

## Project Structure

    search_engine/
    ├── src/          # Source code
    ├── tests/        # Test suite
    ├── data/         # Generated index file (git-ignored)
    ├── requirements.txt
    └── README.md

## Setup

    pip install -r requirements.txt

## Usage

    python src/main.py

*Full usage instructions to be added once implementation is complete.*
