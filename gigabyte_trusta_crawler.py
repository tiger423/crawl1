#!/usr/bin/env python3
"""
GIGABYTE TRUSTA T7P5 Web Crawler
Scrapes https://www.gigabyte.com/Enterprise/AI-Server for TRUSTA or T7P5 information
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GigabyteTrustaCrawler:
    def __init__(self):
        self.base_url = "https://www.gigabyte.com"
        self.target_url = "https://www.gigabyte.com/Enterprise/AI-Server"
        self.search_terms = ["TRUSTA", "T7P5", "trusta", "t7p5"]
        self.results = {
            "found_mentions": [],
            "product_pages_checked": [],
            "total_pages_scanned": 0,
            "search_summary": {}
        }
        self.driver = None
        
    def setup_driver(self):
        """Setup headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            return False
    
    def accept_cookies(self):
        """Accept cookies if cookie banner is present"""
        try:
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(@class, 'accept')]"))
            )
            accept_button.click()
            logger.info("Accepted cookies")
            time.sleep(2)
        except TimeoutException:
            logger.info("No cookie banner found or already accepted")
        except Exception as e:
            logger.warning(f"Error handling cookies: {e}")
    
    def search_text_for_terms(self, text, source_url=""):
        """Search text for TRUSTA or T7P5 mentions"""
        found_terms = []
        text_lower = text.lower()
        
        for term in self.search_terms:
            if term.lower() in text_lower:
                pattern = re.compile(f'.{{0,100}}{re.escape(term.lower())}.{{0,100}}', re.IGNORECASE)
                matches = pattern.findall(text)
                for match in matches:
                    found_terms.append({
                        "term": term,
                        "context": match.strip(),
                        "source_url": source_url
                    })
        
        return found_terms
    
    def extract_product_links(self):
        """Extract all product page links from the main AI Server page"""
        product_links = []
        try:
            learn_more_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/Enterprise/') and (contains(text(), 'Learn More') or contains(@title, 'G') or contains(@title, 'R'))]")
            
            for link in learn_more_links:
                href = link.get_attribute('href')
                title = link.get_attribute('title') or link.text
                if href and href not in [pl['url'] for pl in product_links]:
                    product_links.append({
                        'url': href,
                        'title': title.strip()
                    })
            
            product_page_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/Enterprise/GPU-Server/') or contains(@href, '/Enterprise/Rack-Server/')]")
            
            for link in product_page_links:
                href = link.get_attribute('href')
                title = link.get_attribute('title') or link.text
                if href and href not in [pl['url'] for pl in product_links]:
                    product_links.append({
                        'url': href,
                        'title': title.strip()
                    })
            
            logger.info(f"Found {len(product_links)} product links")
            return product_links
            
        except Exception as e:
            logger.error(f"Error extracting product links: {e}")
            return []
    
    def scrape_page_content(self, url, page_title=""):
        """Scrape content from a single page"""
        try:
            logger.info(f"Scraping page: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            if not page_title:
                try:
                    page_title = self.driver.title
                except:
                    page_title = "Unknown"
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            found_terms = self.search_text_for_terms(page_text, url)
            
            if found_terms:
                logger.info(f"Found {len(found_terms)} mentions on {url}")
                self.results["found_mentions"].extend(found_terms)
            
            storage_keywords = ["storage", "ssd", "nvme", "pcie", "drive", "disk"]
            storage_content = []
            
            try:
                storage_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'storage') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ssd') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'nvme') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pcie')]")
                
                for element in storage_elements:
                    text = element.text.strip()
                    if text and len(text) > 10:  # Avoid empty or very short text
                        storage_content.append(text)
                        storage_found = self.search_text_for_terms(text, url)
                        if storage_found:
                            self.results["found_mentions"].extend(storage_found)
                            
            except Exception as e:
                logger.warning(f"Error searching for storage content: {e}")
            
            page_info = {
                "url": url,
                "title": page_title,
                "has_trusta_mentions": len(found_terms) > 0,
                "storage_content": storage_content[:5],  # Limit to first 5 storage mentions
                "total_text_length": len(page_text)
            }
            
            self.results["product_pages_checked"].append(page_info)
            self.results["total_pages_scanned"] += 1
            
            return page_info
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return None
    
    def scroll_and_load_content(self):
        """Scroll through the main page to load all content"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(5):  # Scroll 5 times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            logger.info("Finished scrolling main page")
            
        except Exception as e:
            logger.warning(f"Error during scrolling: {e}")
    
    def run_crawler(self):
        """Main crawler execution"""
        logger.info("Starting GIGABYTE TRUSTA T7P5 crawler")
        
        if not self.setup_driver():
            return False
        
        try:
            logger.info(f"Loading main page: {self.target_url}")
            self.driver.get(self.target_url)
            time.sleep(5)
            
            self.accept_cookies()
            
            self.scroll_and_load_content()
            
            main_page_info = self.scrape_page_content(self.target_url, "AI Server - GIGABYTE")
            
            product_links = self.extract_product_links()
            
            max_pages = min(20, len(product_links))
            logger.info(f"Will scrape {max_pages} product pages")
            
            for i, product in enumerate(product_links[:max_pages]):
                logger.info(f"Scraping product page {i+1}/{max_pages}: {product['title']}")
                self.scrape_page_content(product['url'], product['title'])
                time.sleep(2)  # Be respectful to the server
            
            self.generate_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def generate_summary(self):
        """Generate summary of findings"""
        total_mentions = len(self.results["found_mentions"])
        pages_with_mentions = len([p for p in self.results["product_pages_checked"] if p["has_trusta_mentions"]])
        
        self.results["search_summary"] = {
            "total_mentions_found": total_mentions,
            "pages_with_mentions": pages_with_mentions,
            "total_pages_scanned": self.results["total_pages_scanned"],
            "search_terms": self.search_terms
        }
        
        logger.info(f"Crawling complete. Found {total_mentions} mentions across {pages_with_mentions} pages")
    
    def display_results(self):
        """Display the crawling results"""
        print("\n" + "="*80)
        print("GIGABYTE TRUSTA T7P5 CRAWLER RESULTS")
        print("="*80)
        
        summary = self.results["search_summary"]
        print(f"\nSUMMARY:")
        print(f"- Total pages scanned: {summary['total_pages_scanned']}")
        print(f"- Total mentions found: {summary['total_mentions_found']}")
        print(f"- Pages with mentions: {summary['pages_with_mentions']}")
        print(f"- Search terms: {', '.join(summary['search_terms'])}")
        
        if self.results["found_mentions"]:
            print(f"\nFOUND MENTIONS:")
            print("-" * 50)
            for i, mention in enumerate(self.results["found_mentions"], 1):
                print(f"\n{i}. Term: {mention['term']}")
                print(f"   Source: {mention['source_url']}")
                print(f"   Context: {mention['context']}")
        else:
            print(f"\nNO MENTIONS FOUND:")
            print("-" * 50)
            print("No references to TRUSTA or T7P5 were found on the scanned pages.")
            print("This could mean:")
            print("- The products are not featured on the AI Server pages")
            print("- The products are mentioned in sections not accessible to the crawler")
            print("- The products use different naming conventions on the website")
        
        print(f"\nPAGES SCANNED:")
        print("-" * 50)
        for page in self.results["product_pages_checked"]:
            status = "✓ HAS MENTIONS" if page["has_trusta_mentions"] else "○ No mentions"
            print(f"{status} - {page['title']} ({page['url']})")
            if page["storage_content"]:
                print(f"    Storage content found: {len(page['storage_content'])} items")
        
        print("\n" + "="*80)
    
    def save_results(self, filename="gigabyte_trusta_results.json"):
        """Save results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {filename}")
            print(f"\nResults saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def main():
    """Main function"""
    crawler = GigabyteTrustaCrawler()
    
    print("GIGABYTE TRUSTA T7P5 Web Crawler")
    print("Searching for TRUSTA or T7P5 mentions on GIGABYTE Enterprise AI Server pages")
    print("-" * 80)
    
    success = crawler.run_crawler()
    
    if success:
        crawler.display_results()
        crawler.save_results()
    else:
        print("Crawler failed to complete successfully. Check the logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
