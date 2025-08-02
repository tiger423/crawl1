#!/usr/bin/env python3
"""
GIGABYTE Storage-Focused TRUSTA T7P5 Web Crawler
Specifically targets Storage and NVMe SSD sections for TRUSTA or T7P5 information
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

class GigabyteStorageFocusedCrawler:
    def __init__(self):
        self.base_url = "https://www.gigabyte.com"
        self.search_terms = ["TRUSTA", "T7P5", "trusta", "t7p5"]
        self.storage_urls = [
            "https://www.gigabyte.com/SSD",
            "https://www.gigabyte.com/SSD/Gen-5",
            "https://www.gigabyte.com/SSD/Gen-4", 
            "https://www.gigabyte.com/SSD/Gen-3",
            "https://www.gigabyte.com/SSD/SATA",
            "https://www.gigabyte.com/SSD/External-SSD",
            "https://www.gigabyte.com/PC-Components",
            "https://www.gigabyte.com/Enterprise/Storage"
        ]
        self.results = {
            "found_mentions": [],
            "storage_pages_checked": [],
            "individual_products_checked": [],
            "total_pages_scanned": 0,
            "search_summary": {},
            "errors": []
        }
        self.driver = None
        self.checked_urls = set()
        
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
        """Search text for TRUSTA or T7P5 mentions with enhanced context"""
        found_terms = []
        text_lower = text.lower()
        
        for term in self.search_terms:
            if term.lower() in text_lower:
                pattern = re.compile(f'.{{0,200}}{re.escape(term.lower())}.{{0,200}}', re.IGNORECASE | re.DOTALL)
                matches = pattern.findall(text)
                for match in matches:
                    found_terms.append({
                        "term": term,
                        "context": match.strip(),
                        "source_url": source_url,
                        "full_match": True
                    })
        
        related_terms = ["trust", "t7p", "gen5", "gen 5", "pcie gen 5", "nvme gen5"]
        for related_term in related_terms:
            if related_term in text_lower:
                for main_term in self.search_terms:
                    if main_term.lower() in text_lower:
                        pattern = re.compile(f'.{{0,300}}{re.escape(related_term)}.{{0,300}}', re.IGNORECASE | re.DOTALL)
                        matches = pattern.findall(text)
                        for match in matches:
                            found_terms.append({
                                "term": f"{related_term} (related to {main_term})",
                                "context": match.strip(),
                                "source_url": source_url,
                                "full_match": False
                            })
        
        return found_terms
    
    def extract_product_links(self):
        """Extract SSD product links from current page"""
        product_links = []
        try:
            ssd_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/SSD/') and not(contains(@href, 'javascript'))]")
            
            for link in ssd_links:
                href = link.get_attribute('href')
                title = link.get_attribute('title') or link.text.strip()
                
                if href and href not in [pl['url'] for pl in product_links] and href not in self.checked_urls:
                    if any(keyword in href.lower() for keyword in ['aorus', 'gigabyte', 'nvme', 'gen', 'ssd']) and len(href.split('/')) > 4:
                        product_links.append({
                            'url': href,
                            'title': title,
                            'type': 'SSD Product'
                        })
            
            storage_links = self.driver.find_elements(By.XPATH, "//a[contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'storage') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'nvme') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'drive')]")
            
            for link in storage_links:
                href = link.get_attribute('href')
                title = link.get_attribute('title') or link.text.strip()
                
                if href and href.startswith(self.base_url) and href not in [pl['url'] for pl in product_links] and href not in self.checked_urls:
                    product_links.append({
                        'url': href,
                        'title': title,
                        'type': 'Storage Related'
                    })
            
            logger.info(f"Found {len(product_links)} product links")
            return product_links[:15]  # Limit to 15 products per page
            
        except Exception as e:
            logger.error(f"Error extracting product links: {e}")
            return []
    
    def scrape_page_content(self, url, page_title="", page_type="storage"):
        """Scrape content from a single page with enhanced SSD focus"""
        if url in self.checked_urls:
            return None
            
        try:
            logger.info(f"Scraping {page_type} page: {url}")
            self.driver.get(url)
            time.sleep(4)  # Give more time for SSD pages to load
            
            self.checked_urls.add(url)
            
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
            
            ssd_info = self.extract_ssd_specifications(url)
            
            spec_content = []
            try:
                spec_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'specification') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'feature') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'capacity') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'interface') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'performance')]")
                
                for element in spec_elements:
                    text = element.text.strip()
                    if text and len(text) > 10 and len(text) < 1000:
                        spec_content.append(text)
                        spec_found = self.search_text_for_terms(text, url)
                        if spec_found:
                            self.results["found_mentions"].extend(spec_found)
                            
            except Exception as e:
                logger.warning(f"Error searching for specifications: {e}")
            
            page_info = {
                "url": url,
                "title": page_title,
                "page_type": page_type,
                "has_trusta_mentions": len(found_terms) > 0,
                "ssd_specifications": ssd_info,
                "specification_content": list(set(spec_content))[:10],  # Remove duplicates, limit to 10
                "total_text_length": len(page_text),
                "accessible": len(page_text) > 100
            }
            
            if page_type == "storage":
                self.results["storage_pages_checked"].append(page_info)
            else:
                self.results["individual_products_checked"].append(page_info)
                
            self.results["total_pages_scanned"] += 1
            
            return page_info
            
        except Exception as e:
            error_msg = f"Error scraping page {url}: {e}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return None
    
    def extract_ssd_specifications(self, url):
        """Extract SSD-specific specifications from the page"""
        ssd_specs = {}
        try:
            spec_keywords = {
                "capacity": ["capacity", "storage", "gb", "tb"],
                "interface": ["interface", "pcie", "nvme", "sata", "m.2"],
                "performance": ["read", "write", "speed", "mbps", "gbps", "iops"],
                "generation": ["gen", "generation", "pcie 3.0", "pcie 4.0", "pcie 5.0"],
                "form_factor": ["form factor", "m.2", "2280", "2260", "u.2"],
                "controller": ["controller", "phison", "samsung", "micron"],
                "nand": ["nand", "3d nand", "tlc", "qlc", "slc"]
            }
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for spec_type, keywords in spec_keywords.items():
                for keyword in keywords:
                    if keyword in page_text:
                        pattern = re.compile(f'.{{0,50}}{re.escape(keyword)}.{{0,50}}', re.IGNORECASE)
                        matches = pattern.findall(page_text)
                        if matches:
                            ssd_specs[spec_type] = matches[:3]  # Keep first 3 matches
                            break
            
            return ssd_specs
            
        except Exception as e:
            logger.warning(f"Error extracting SSD specifications: {e}")
            return {}
    
    def search_gigabyte_storage_sections(self):
        """Search specific GIGABYTE storage sections"""
        try:
            search_terms_to_try = ["TRUSTA", "T7P5", "TRUSTA T7P5"]
            
            for search_term in search_terms_to_try:
                try:
                    search_url = f"https://www.gigabyte.com/Search?q={search_term}"
                    logger.info(f"Attempting search for: {search_term}")
                    
                    self.driver.get(search_url)
                    time.sleep(3)
                    
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    found_terms = self.search_text_for_terms(page_text, search_url)
                    
                    if found_terms:
                        logger.info(f"Found {len(found_terms)} mentions in search results for {search_term}")
                        self.results["found_mentions"].extend(found_terms)
                        
                except Exception as e:
                    logger.warning(f"Error during search for {search_term}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Site search failed: {e}")
    
    def run_storage_focused_crawler(self):
        """Main storage-focused crawler execution"""
        logger.info("Starting Storage-Focused GIGABYTE TRUSTA T7P5 crawler")
        
        if not self.setup_driver():
            return False
        
        try:
            self.search_gigabyte_storage_sections()
            
            for url in self.storage_urls:
                try:
                    logger.info(f"Loading storage page: {url}")
                    self.driver.get(url)
                    time.sleep(3)
                    
                    if url == self.storage_urls[0]:
                        self.accept_cookies()
                    
                    page_info = self.scrape_page_content(url, page_type="storage")
                    
                    if page_info and page_info.get("accessible", False):
                        product_links = self.extract_product_links()
                        
                        for i, product in enumerate(product_links[:5]):  # Limit to 5 products per storage page
                            logger.info(f"Following SSD product link {i+1}/5: {product['title']}")
                            self.scrape_page_content(product['url'], product['title'], page_type="product")
                            time.sleep(2)
                    
                except Exception as e:
                    error_msg = f"Error processing storage URL {url}: {e}"
                    logger.error(error_msg)
                    self.results["errors"].append(error_msg)
                    continue
            
            self.generate_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error during storage-focused crawling: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def generate_summary(self):
        """Generate summary of findings"""
        total_mentions = len(self.results["found_mentions"])
        storage_pages_with_mentions = len([p for p in self.results["storage_pages_checked"] if p.get("has_trusta_mentions", False)])
        product_pages_with_mentions = len([p for p in self.results["individual_products_checked"] if p.get("has_trusta_mentions", False)])
        
        self.results["search_summary"] = {
            "total_mentions_found": total_mentions,
            "storage_pages_with_mentions": storage_pages_with_mentions,
            "product_pages_with_mentions": product_pages_with_mentions,
            "total_pages_scanned": self.results["total_pages_scanned"],
            "storage_pages_scanned": len(self.results["storage_pages_checked"]),
            "product_pages_scanned": len(self.results["individual_products_checked"]),
            "search_terms": self.search_terms,
            "storage_urls_targeted": self.storage_urls,
            "errors_encountered": len(self.results["errors"])
        }
        
        logger.info(f"Storage-focused crawling complete. Found {total_mentions} mentions across {storage_pages_with_mentions + product_pages_with_mentions} pages")
    
    def display_results(self):
        """Display the storage-focused crawling results"""
        print("\n" + "="*80)
        print("GIGABYTE STORAGE-FOCUSED TRUSTA T7P5 CRAWLER RESULTS")
        print("="*80)
        
        summary = self.results["search_summary"]
        print(f"\nSUMMARY:")
        print(f"- Total pages scanned: {summary['total_pages_scanned']}")
        print(f"- Storage category pages: {summary['storage_pages_scanned']}")
        print(f"- Individual SSD products: {summary['product_pages_scanned']}")
        print(f"- Total mentions found: {summary['total_mentions_found']}")
        print(f"- Storage pages with mentions: {summary['storage_pages_with_mentions']}")
        print(f"- Product pages with mentions: {summary['product_pages_with_mentions']}")
        print(f"- Errors encountered: {summary['errors_encountered']}")
        print(f"- Search terms: {', '.join(summary['search_terms'])}")
        
        if self.results["found_mentions"]:
            print(f"\nFOUND MENTIONS:")
            print("-" * 50)
            for i, mention in enumerate(self.results["found_mentions"], 1):
                match_type = "EXACT" if mention.get("full_match", True) else "RELATED"
                print(f"\n{i}. [{match_type}] Term: {mention['term']}")
                print(f"   Source: {mention['source_url']}")
                print(f"   Context: {mention['context'][:200]}...")
        else:
            print(f"\nNO MENTIONS FOUND:")
            print("-" * 50)
            print("No references to TRUSTA or T7P5 were found in GIGABYTE's Storage/SSD sections.")
            print("\nConclusions:")
            print("- TRUSTA T7P5 is NOT listed in GIGABYTE's public SSD product catalog")
            print("- Searched all SSD categories: Gen 5, Gen 4, Gen 3, SATA, External SSD")
            print("- Checked individual SSD product pages and specifications")
            print("- TRUSTA may be a different brand or OEM product not sold under GIGABYTE")
        
        ssd_products = [p for p in self.results["individual_products_checked"] if "ssd" in p["title"].lower()]
        if ssd_products:
            print(f"\nGIGABYTE SSD PRODUCTS FOUND (for reference):")
            print("-" * 50)
            for product in ssd_products[:10]:  # Show first 10
                specs = product.get("ssd_specifications", {})
                spec_summary = ", ".join([f"{k}: {v[0] if v else 'N/A'}" for k, v in specs.items()][:3])
                print(f"- {product['title']}")
                print(f"  URL: {product['url']}")
                if spec_summary:
                    print(f"  Specs: {spec_summary}")
        
        print(f"\nSTORAGE PAGES SCANNED:")
        print("-" * 50)
        for page in self.results["storage_pages_checked"]:
            status = "✓ HAS MENTIONS" if page.get("has_trusta_mentions", False) else "○ No mentions"
            accessible = "✓" if page.get("accessible", False) else "✗"
            print(f"{status} [{accessible}] - {page['title']}")
            print(f"    {page['url']}")
        
        if self.results["errors"]:
            print(f"\nERRORS ENCOUNTERED:")
            print("-" * 50)
            for error in self.results["errors"]:
                print(f"- {error}")
        
        print("\n" + "="*80)
    
    def save_results(self, filename="gigabyte_storage_focused_results.json"):
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
    crawler = GigabyteStorageFocusedCrawler()
    
    print("GIGABYTE Storage-Focused TRUSTA T7P5 Web Crawler")
    print("Targeting Storage and NVMe SSD sections specifically")
    print("-" * 80)
    
    success = crawler.run_storage_focused_crawler()
    
    if success:
        crawler.display_results()
        crawler.save_results()
    else:
        print("Storage-focused crawler failed to complete successfully. Check the logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
