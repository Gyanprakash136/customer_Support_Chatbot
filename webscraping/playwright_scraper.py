#!/usr/bin/env python3
# enhanced_playwright_scraper.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import json
import os
import argparse
import logging
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Optional, Union
import re
import csv


class WebScraper:
    def __init__(
            self,
            output_dir: str = "scraped_data",
            wait_time: int = 2,
            headless: bool = True,
            timeout: int = 30000,
            user_agent: Optional[str] = None,
            screenshot: bool = False,
            log_level: str = "INFO",
    ):
        """Initialize the web scraper with configuration options.

        Args:
            output_dir: Directory to save scraped data
            wait_time: Time to wait after page load for dynamic content (seconds)
            headless: Whether to run browser in headless mode
            timeout: Page navigation timeout in milliseconds
            user_agent: Custom user agent string
            screenshot: Whether to save screenshots of pages
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.output_dir = output_dir
        self.wait_time = wait_time
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent
        self.screenshot = screenshot

        # Setup logging
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Convert string to valid filename by removing illegal characters."""
        # Replace illegal filename characters with underscores
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def _extract_metadata(self, page) -> Dict:
        """Extract metadata from the page."""
        metadata = {}

        # Extract meta tags
        for meta in page.query_selector_all("meta"):
            name = meta.get_attribute("name") or meta.get_attribute("property")
            content = meta.get_attribute("content")
            if name and content:
                metadata[name] = content

        # Extract structured data (JSON-LD)
        json_ld_scripts = page.query_selector_all('script[type="application/ld+json"]')
        json_ld_data = []
        for script in json_ld_scripts:
            try:
                script_content = script.inner_text()
                if script_content:
                    json_ld_data.append(json.loads(script_content))
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse JSON-LD data")

        if json_ld_data:
            metadata["json_ld"] = json_ld_data

        return metadata

    def _extract_links(self, page) -> List[Dict]:
        """Extract all links from the page."""
        links = []
        for link in page.query_selector_all("a[href]"):
            href = link.get_attribute("href")
            text = link.inner_text().strip()
            if href:
                links.append({
                    "url": href,
                    "text": text if text else None
                })
        return links

    def _extract_images(self, page) -> List[Dict]:
        """Extract all images from the page."""
        images = []
        for img in page.query_selector_all("img[src]"):
            src = img.get_attribute("src")
            alt = img.get_attribute("alt")
            if src:
                images.append({
                    "src": src,
                    "alt": alt if alt else None
                })
        return images

    def _extract_main_content(self, page) -> Dict:
        """Extract main content based on common selectors."""
        main_content = {
            "title": page.title(),
            "text": page.inner_text("body")
        }

        # Try to extract more specific content areas
        content_selectors = [
            "main", "article", "#content", ".content",
            "#main", ".main", ".post", ".article"
        ]

        for selector in content_selectors:
            content_element = page.query_selector(selector)
            if content_element:
                main_content["main_content"] = content_element.inner_text().strip()
                break

        # Extract headings
        headings = []
        for heading_level in range(1, 7):
            for heading in page.query_selector_all(f"h{heading_level}"):
                headings.append({
                    "level": heading_level,
                    "text": heading.inner_text().strip()
                })

        if headings:
            main_content["headings"] = headings

        return main_content

    def scrape_url(self, url: str) -> Dict:
        """Scrape a single URL and return the extracted data."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        result = {
            "url": url,
            "domain": domain,
            "timestamp": timestamp,
            "status": "failed",  # Default to failed, update on success
        }

        try:
            with sync_playwright() as p:
                # Configure browser
                browser_type = p.chromium
                browser_args = {
                    "headless": self.headless,
                }

                browser = browser_type.launch(**browser_args)

                # Configure page
                context_args = {
                    "viewport": {"width": 1280, "height": 800},
                }

                if self.user_agent:
                    context_args["user_agent"] = self.user_agent

                context = browser.new_context(**context_args)
                page = context.new_page()

                # Set timeout for navigation
                page.set_default_timeout(self.timeout)

                # Navigate to the URL
                self.logger.info(f"Visiting: {url}")
                response = page.goto(url, wait_until="networkidle")

                # Check if navigation was successful
                if not response:
                    self.logger.error(f"Failed to get response from {url}")
                    return result

                status_code = response.status
                result["status_code"] = status_code

                if status_code >= 400:
                    self.logger.error(f"Received HTTP {status_code} from {url}")
                    return result

                # Wait for dynamic content
                if self.wait_time > 0:
                    self.logger.debug(f"Waiting {self.wait_time}s for dynamic content...")
                    time.sleep(self.wait_time)

                # Take screenshot if requested
                if self.screenshot:
                    screenshot_path = os.path.join(
                        self.output_dir,
                        f"{self._sanitize_filename(domain)}_{timestamp}.png"
                    )
                    page.screenshot(path=screenshot_path, full_page=True)
                    self.logger.info(f"Screenshot saved to {screenshot_path}")
                    result["screenshot_path"] = screenshot_path

                # Extract data
                result.update({
                    "title": page.title(),
                    "metadata": self._extract_metadata(page),
                    "content": self._extract_main_content(page),
                    "links": self._extract_links(page),
                    "images": self._extract_images(page),
                    "html": page.content(),
                    "status": "success"
                })

                browser.close()

        except PlaywrightTimeoutError:
            self.logger.error(f"Timeout when accessing {url}")
            result["error"] = "Timeout error"
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            result["error"] = str(e)

        return result

    def save_result(self, result: Dict, format: str = "json") -> str:
        """Save the scraping results to file in the specified format."""
        domain = self._sanitize_filename(result.get("domain", "unknown"))
        timestamp = result.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))

        if format == "json":
            file_path = os.path.join(self.output_dir, f"{domain}_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        elif format == "txt":
            file_path = os.path.join(self.output_dir, f"{domain}_{timestamp}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"URL: {result.get('url')}\n")
                f.write(f"Title: {result.get('title')}\n")
                f.write(f"Status: {result.get('status')}\n\n")

                if "content" in result and "main_content" in result["content"]:
                    f.write("--- CONTENT ---\n")
                    f.write(result["content"]["main_content"])
                elif "content" in result and "text" in result["content"]:
                    f.write("--- CONTENT ---\n")
                    f.write(result["content"]["text"][:2000] + "...")  # Truncate long content

        elif format == "csv":
            # For CSV, we'll just save basic info and the full data remains in JSON
            file_path = os.path.join(self.output_dir, "scraping_results.csv")

            # Check if file exists to write headers
            file_exists = os.path.isfile(file_path)

            with open(file_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "url", "domain", "title", "status", "json_file"])

                json_file = f"{domain}_{timestamp}.json"
                # Save the JSON file as well
                with open(os.path.join(self.output_dir, json_file), "w", encoding="utf-8") as jf:
                    json.dump(result, jf, indent=2, ensure_ascii=False)

                writer.writerow([
                    timestamp,
                    result.get("url", ""),
                    result.get("domain", ""),
                    result.get("title", ""),
                    result.get("status", "unknown"),
                    json_file
                ])
        else:
            raise ValueError(f"Unsupported output format: {format}")

        self.logger.info(f"Saved results to {file_path}")
        return file_path

    def scrape_multiple(self, urls: List[str], format: str = "json") -> List[str]:
        """Scrape multiple URLs and save results."""
        results_files = []

        for url in urls:
            try:
                result = self.scrape_url(url)
                file_path = self.save_result(result, format)
                results_files.append(file_path)
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {str(e)}")

        return results_files


def main():
    parser = argparse.ArgumentParser(description="Enhanced web scraper using Playwright")
    parser.add_argument("urls", nargs="+", help="Website URL(s) to scrape")
    parser.add_argument("--output", "-o", default="scraped_data", help="Output folder")
    parser.add_argument("--wait", "-w", type=int, default=2, help="Wait time after page load (seconds)")
    parser.add_argument("--format", "-f", choices=["json", "txt", "csv"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--screenshot", "-s", action="store_true", help="Save page screenshots")
    parser.add_argument("--visible", "-v", action="store_true", help="Run browser in visible mode")
    parser.add_argument("--timeout", "-t", type=int, default=30000, help="Page load timeout (milliseconds)")
    parser.add_argument("--user-agent", "-u", help="Custom user agent string")
    parser.add_argument("--log-level", "-l", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        default="INFO", help="Logging level")

    args = parser.parse_args()

    scraper = WebScraper(
        output_dir=args.output,
        wait_time=args.wait,
        headless=not args.visible,
        timeout=args.timeout,
        user_agent=args.user_agent,
        screenshot=args.screenshot,
        log_level=args.log_level,
    )

    if len(args.urls) == 1:
        # Single URL mode
        result = scraper.scrape_url(args.urls[0])
        scraper.save_result(result, args.format)
    else:
        # Multiple URL mode
        scraper.scrape_multiple(args.urls, args.format)


if __name__ == "__main__":
    main()