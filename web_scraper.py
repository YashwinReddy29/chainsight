#!/usr/bin/env python3
"""
Web scraper script demonstrating HTTP requests and HTML parsing.
Uses requests library for HTTP operations and beautifulsoup4 for HTML parsing.
"""

import requests  # CHAINSIGHT-REVIEW
from bs4 import BeautifulSoup  # CHAINSIGHT-REVIEW
from typing import Optional, Dict, List
import sys


def fetch_webpage(url: str, timeout: int = 10) -> Optional[requests.Response]:
    """
    Fetch a webpage using HTTP GET request.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Response object if successful, None otherwise
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def parse_html(html_content: str) -> BeautifulSoup:
    """
    Parse HTML content using BeautifulSoup.
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        BeautifulSoup object for parsing
    """
    return BeautifulSoup(html_content, 'html.parser')


def extract_links(soup: BeautifulSoup) -> List[str]:
    """
    Extract all links from parsed HTML.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        List of URLs found in the page
    """
    links = []
    for link in soup.find_all('a', href=True):
        links.append(link['href'])
    return links


def extract_text(soup: BeautifulSoup) -> str:
    """
    Extract all text content from parsed HTML.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Cleaned text content
    """
    return soup.get_text(strip=True, separator=' ')


def extract_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract metadata from HTML head section.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Dictionary of metadata
    """
    metadata = {}
    
    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        metadata['title'] = title_tag.get_text()
    
    # Extract meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        if name and content:
            metadata[name] = content
    
    return metadata


def main():
    """
    Main function demonstrating web scraping functionality.
    """
    # Example URL - replace with actual target
    url = "https://example.com"
    
    print(f"Fetching webpage: {url}")
    response = fetch_webpage(url)
    
    if not response:
        print("Failed to fetch webpage")
        return 1
    
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('content-type')}")
    
    # Parse HTML
    soup = parse_html(response.text)
    
    # Extract metadata
    print("\n=== Metadata ===")
    metadata = extract_metadata(soup)
    for key, value in metadata.items():
        print(f"{key}: {value}")
    
    # Extract links
    print("\n=== Links Found ===")
    links = extract_links(soup)
    for i, link in enumerate(links[:10], 1):  # Show first 10 links
        print(f"{i}. {link}")
    print(f"Total links: {len(links)}")
    
    # Extract text content
    print("\n=== Text Content (first 500 chars) ===")
    text = extract_text(soup)
    print(text[:500])
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
