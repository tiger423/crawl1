#!/usr/bin/env python3
"""
Enhanced GIGABYTE TRUSTA T7P5 Web Crawler
Searches multiple sections of GIGABYTE website for TRUSTA or T7P5 information
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

class EnhancedGigabyteTrustaCrawler:
    def __init__(self):
        self.base_url = "https://www.gigabyte.com"
        self.search_terms = ["TRUSTA", "T7P5", "trusta", "t7p5"]
        self.target_urls = [
            "https://www.gigabyte.com/Enterprise/AI-Server",
            "https://www.gigabyte.com/Enterprise",
            "https://www.gigabyte.com/SSD",
            "https://www.gigabyte.com/Storage",
            "https://www.gigabyte.com/Enterprise/Storage",
            "https://www.gigabyte.com/Enterprise/SSD",
            "https://www.gigabyte.com/Products"
        ]
        self.results = {
            "found_mentions": [],
            "pages_checked": [],
            "total_pages_scanned": 0,
            "search_summary": {},
            "errors": []
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
            accept_button = WebDriverWait(self.driver, 5).until(
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
                pattern = re.compile(f'.{{0,150}}{re.escape(term.lower())}.{{0,150}}', re.IGNORECASE)
                matches = pattern.findall(text)
                for match in matches:
                    found_terms.append({
                        "term": term,
                        "context": match.strip(),
                        "source_url": source_url
                    })
        
        return found_terms
    
    def extract_links_from_page(self, base_url):
        """Extract relevant links from current page"""
        links = []
        try:
            storage_keywords = ["storage", "ssd", "nvme", "enterprise", "server", "drive"]
            
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in all_links:
                href = link.get_attribute('href')
                text = link.text.lower().strip()
                title = link.get_attribute('title')
                
                if href and href.startswith(self.base_url):
                    link_text_combined = f"{text} {title or ''}".lower()
                    if any(keyword in link_text_combined or keyword in href.lower() for keyword in storage_keywords):
                        if href not in [l['url'] for l in links]:
                            links.append({
                                'url': href,
                                'text': text,
                                'title': title or text
                            })
            
            logger.info(f"Found {len(links)} relevant links on {base_url}")
            return links[:10]  # Limit to first 10 relevant links
            
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
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
            
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
            except:
                page_text = ""
            
            found_terms = self.search_text_for_terms(page_text, url)
            
            if found_terms:
                logger.info(f"Found {len(found_terms)} mentions on {url}")
                self.results["found_mentions"].extend(found_terms)
            
            storage_content = []
            storage_keywords = ["storage", "ssd", "nvme", "pcie", "drive", "disk", "gen 5", "gen5"]
            
            try:
                for keyword in storage_keywords:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                    
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10 and len(text) < 500:
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
                "storage_content": list(set(storage_content))[:5],  # Remove duplicates, limit to 5
                "total_text_length": len(page_text),
                "accessible": len(page_text) > 100  # Consider page accessible if it has substantial content
            }
            
            self.results["pages_checked"].append(page_info)
            self.results["total_pages_scanned"] += 1
            
            return page_info
            
        except Exception as e:
            error_msg = f"Error scraping page {url}: {e}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return None
    
    def search_gigabyte_site(self):
        """Search GIGABYTE site using site search"""
        try:
            search_url = "https://www.gigabyte.com/Search"
            logger.info(f"Attempting site search at {search_url}")
            
            self.driver.get(search_url)
            time.sleep(3)
            
            search_boxes = self.driver.find_elements(By.XPATH, "//input[@type='search' or @type='text' or contains(@placeholder, 'search') or contains(@name, 'search')]")
            
            for search_term in ["TRUSTA", "T7P5"]:
                for search_box in search_boxes:
                    try:
                        search_box.clear()
                        search_box.send_keys(search_term)
                        
                        search_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Search') or @type='submit'] | //input[@type='submit']")
                        
                        if search_buttons:
                            search_buttons[0].click()
                            time.sleep(3)
                            
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text
                            found_terms = self.search_text_for_terms(page_text, f"{search_url}?q={search_term}")
                            
                            if found_terms:
                                logger.info(f"Found {len(found_terms)} mentions in search results for {search_term}")
                                self.results["found_mentions"].extend(found_terms)
                            
                            break
                    except Exception as e:
                        logger.warning(f"Error during site search for {search_term}: {e}")
                        continue
                        
        except Exception as e:
            logger.warning(f"Site search failed: {e}")
    
    def run_enhanced_crawler(self):
        """Main enhanced crawler execution"""
        logger.info("Starting Enhanced GIGABYTE TRUSTA T7P5 crawler")
        
        if not self.setup_driver():
            return False
        
        try:
            self.search_gigabyte_site()
            
            for url in self.target_urls:
                try:
                    logger.info(f"Loading page: {url}")
                    self.driver.get(url)
                    time.sleep(3)
                    
                    if url == self.target_urls[0]:
                        self.accept_cookies()
                    
                    page_info = self.scrape_page_content(url)
                    
                    if page_info and page_info.get("accessible", False):
                        relevant_links = self.extract_links_from_page(url)
                        
                        for i, link in enumerate(relevant_links[:3]):  # Limit to 3 links per main page
                            logger.info(f"Following relevant link {i+1}/3: {link['title']}")
                            self.scrape_page_content(link['url'], link['title'])
                            time.sleep(2)
                    
                except Exception as e:
                    error_msg = f"Error processing {url}: {e}"
                    logger.error(error_msg)
                    self.results["errors"].append(error_msg)
                    continue
            
            self.generate_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error during enhanced crawling: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def generate_summary(self):
        """Generate summary of findings"""
        total_mentions = len(self.results["found_mentions"])
        pages_with_mentions = len([p for p in self.results["pages_checked"] if p.get("has_trusta_mentions", False)])
        accessible_pages = len([p for p in self.results["pages_checked"] if p.get("accessible", False)])
        
        self.results["search_summary"] = {
            "total_mentions_found": total_mentions,
            "pages_with_mentions": pages_with_mentions,
            "total_pages_scanned": self.results["total_pages_scanned"],
            "accessible_pages": accessible_pages,
            "search_terms": self.search_terms,
            "target_urls": self.target_urls,
            "errors_encountered": len(self.results["errors"])
        }
        
        logger.info(f"Enhanced crawling complete. Found {total_mentions} mentions across {pages_with_mentions} pages")
    
    def display_results(self):
        """Display the enhanced crawling results"""
        print("\n" + "="*80)
        print("ENHANCED GIGABYTE TRUSTA T7P5 CRAWLER RESULTS")
        print("="*80)
        
        summary = self.results["search_summary"]
        print(f"\nSUMMARY:")
        print(f"- Total pages scanned: {summary['total_pages_scanned']}")
        print(f"- Accessible pages: {summary['accessible_pages']}")
        print(f"- Total mentions found: {summary['total_mentions_found']}")
        print(f"- Pages with mentions: {summary['pages_with_mentions']}")
        print(f"- Errors encountered: {summary['errors_encountered']}")
        print(f"- Search terms: {', '.join(summary['search_terms'])}")
        print(f"- Target URLs searched: {len(summary['target_urls'])}")
        
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
            print("\nPossible reasons:")
            print("- The TRUSTA T7P5 products are not featured on GIGABYTE's website")
            print("- The products are mentioned using different naming conventions")
            print("- The products are in sections not accessible to web crawlers")
            print("- The products may be OEM/private label and not publicly listed")
        
        storage_pages = [p for p in self.results["pages_checked"] if p.get("storage_content")]
        if storage_pages:
            print(f"\nSTORAGE-RELATED CONTENT FOUND:")
            print("-" * 50)
            for page in storage_pages:
                print(f"\nPage: {page['title']} ({page['url']})")
                for content in page['storage_content']:
                    print(f"  - {content[:100]}...")
        
        print(f"\nPAGES SCANNED:")
        print("-" * 50)
        for page in self.results["pages_checked"]:
            status = "✓ HAS MENTIONS" if page.get("has_trusta_mentions", False) else "○ No mentions"
            accessible = "✓" if page.get("accessible", False) else "✗"
            storage_count = len(page.get("storage_content", []))
            print(f"{status} [{accessible}] - {page['title']} (Storage: {storage_count})")
            print(f"    {page['url']}")
        
        if self.results["errors"]:
            print(f"\nERRORS ENCOUNTERED:")
            print("-" * 50)
            for error in self.results["errors"]:
                print(f"- {error}")
        
        print("\n" + "="*80)
    
    def save_results(self, filename="gigabyte_enhanced_results.json"):
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
    crawler = EnhancedGigabyteTrustaCrawler()
    
    print("Enhanced GIGABYTE TRUSTA T7P5 Web Crawler")
    print("Searching multiple sections of GIGABYTE website for TRUSTA or T7P5 mentions")
    print("-" * 80)
    
    success = crawler.run_enhanced_crawler()
    
    if success:
        crawler.display_results()
        crawler.save_results()
    else:
        print("Enhanced crawler failed to complete successfully. Check the logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
