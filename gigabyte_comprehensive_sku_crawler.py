#!/usr/bin/env python3
"""
Comprehensive GIGABYTE Server SKU TRUSTA Crawler
Searches each server SKU from server-sku.txt across all Enterprise categories
Follows the specific QVL navigation flow to find TRUSTA products
"""

import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class GigabyteComprehensiveSKUCrawler:
    def __init__(self):
        self.base_url = "https://www.gigabyte.com"
        self.enterprise_categories = [
            "/Enterprise/GPU-Server",
            "/Enterprise/General-Purpose-Server", 
            "/Enterprise/AI-Server",
            "/Enterprise/High-Density-Server"
        ]
        self.driver = None
        self.results = {
            "search_metadata": {
                "start_time": datetime.now().isoformat(),
                "total_skus_searched": 0,
                "skus_found": 0,
                "skus_with_qvl": 0,
                "skus_with_trusta": 0,
                "categories_searched": len(self.enterprise_categories)
            },
            "sku_results": {},
            "trusta_findings": [],
            "search_summary": {}
        }
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Error setting up WebDriver: {e}")
            return False
    
    def load_server_skus(self):
        """Load server SKUs from server-sku.txt file"""
        try:
            with open('server-sku.txt', 'r', encoding='utf-8') as f:
                skus = [line.strip() for line in f if line.strip()]
            print(f"✅ Loaded {len(skus)} server SKUs from server-sku.txt")
            return skus
        except FileNotFoundError:
            print("❌ Error: server-sku.txt file not found")
            return []
        except Exception as e:
            print(f"❌ Error loading server SKUs: {e}")
            return []
    
    def search_sku_in_category(self, sku, category_url):
        """Search for a specific SKU in a given category"""
        try:
            full_url = f"{self.base_url}{category_url}"
            print(f"   🔍 Searching in {category_url}")
            
            self.driver.get(full_url)
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            sku_lower = sku.lower()
            
            if sku_lower in page_source:
                print(f"   ✅ Found SKU {sku} in {category_url}")
                return self.find_sku_specific_page(sku, category_url)
            else:
                print(f"   ❌ SKU {sku} not found in {category_url}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error searching {sku} in {category_url}: {e}")
            return None
    
    def find_sku_specific_page(self, sku, category_url):
        """Find the specific product page for the SKU"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            sku_lower = sku.lower()
            
            for link in links:
                href = link.get_attribute("href")
                text = link.text.lower()
                
                if href and (sku_lower in href.lower() or sku_lower in text):
                    print(f"   🎯 Found potential SKU page: {href}")
                    return href
            
            sku_parts = sku.split('-')
            if len(sku_parts) >= 2:
                base_model = '-'.join(sku_parts[:2])  # e.g., G293-S40
                
                for link in links:
                    href = link.get_attribute("href")
                    text = link.text.lower()
                    
                    if href and (base_model.lower() in href.lower() or base_model.lower() in text):
                        print(f"   🎯 Found potential base model page: {href}")
                        return href
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error finding SKU page: {e}")
            return None
    
    def navigate_to_qvl_and_search_trusta(self, sku, product_url):
        """Navigate to QVL page and search for TRUSTA following the specific flow"""
        try:
            print(f"   📋 Navigating to QVL for {sku}")
            self.driver.get(product_url)
            time.sleep(3)
            
            qvl_found = False
            try:
                qvl_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'QVL') or contains(@href, 'QVL') or contains(@href, 'qvl')]")
                if qvl_links:
                    print(f"   ✅ Found QVL navigation link")
                    qvl_links[0].click()
                    time.sleep(3)
                    qvl_found = True
                else:
                    support_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Support') or contains(@href, 'Support')]")
                    for link in support_links:
                        if 'qvl' in link.get_attribute("href").lower():
                            print(f"   ✅ Found QVL link in Support section")
                            link.click()
                            time.sleep(3)
                            qvl_found = True
                            break
            except Exception as e:
                print(f"   ❌ Error finding QVL link: {e}")
            
            if not qvl_found:
                print(f"   ❌ No QVL page found for {sku}")
                return None
            
            storage_found = False
            try:
                storage_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Storage') or contains(@href, 'Storage')]")
                if storage_links:
                    print(f"   ✅ Found Storage category")
                    storage_links[0].click()
                    time.sleep(3)
                    storage_found = True
            except Exception as e:
                print(f"   ❌ Error finding Storage category: {e}")
            
            if not storage_found:
                print(f"   ❌ No Storage category found for {sku}")
                return None
            
            nvme_found = False
            try:
                nvme_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'NVMe') or contains(text(), 'SSD')]")
                for link in nvme_links:
                    if 'nvme' in link.text.lower() and 'ssd' in link.text.lower():
                        print(f"   ✅ Found NVMe SSD subcategory")
                        link.click()
                        time.sleep(3)
                        nvme_found = True
                        break
            except Exception as e:
                print(f"   ❌ Error finding NVMe SSD subcategory: {e}")
            
            if not nvme_found:
                print(f"   ❌ No NVMe SSD subcategory found for {sku}")
                return None
            
            return self.search_trusta_in_qvl_table(sku)
            
        except Exception as e:
            print(f"   ❌ Error navigating QVL for {sku}: {e}")
            return None
    
    def search_trusta_in_qvl_table(self, sku):
        """Search for TRUSTA products in the QVL table"""
        try:
            print(f"   🔍 Searching for TRUSTA in QVL table")
            
            page_source = self.driver.page_source
            trusta_matches = []
            
            if 'trusta' in page_source.lower() or 't7p5' in page_source.lower():
                print(f"   🎉 FOUND TRUSTA/T7P5 in QVL for {sku}!")
                
                try:
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    for table in tables:
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        for row in rows:
                            row_text = row.text.lower()
                            if 'trusta' in row_text or 't7p5' in row_text:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if cells:
                                    row_data = [cell.text.strip() for cell in cells]
                                    trusta_matches.append({
                                        "sku": sku,
                                        "row_data": row_data,
                                        "raw_text": row.text.strip()
                                    })
                                    print(f"   📋 TRUSTA row: {row.text.strip()}")
                except Exception as e:
                    print(f"   ⚠️ Error extracting table data: {e}")
                
                return {
                    "sku": sku,
                    "trusta_found": True,
                    "matches": trusta_matches,
                    "page_url": self.driver.current_url,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"   ❌ No TRUSTA found in QVL for {sku}")
                return {
                    "sku": sku,
                    "trusta_found": False,
                    "page_url": self.driver.current_url,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"   ❌ Error searching TRUSTA in QVL: {e}")
            return None
    
    def search_single_sku(self, sku):
        """Search for a single SKU across all categories"""
        print(f"\n🔍 Searching SKU: {sku}")
        sku_result = {
            "sku": sku,
            "found_in_categories": [],
            "qvl_accessible": False,
            "trusta_found": False,
            "trusta_data": None,
            "search_timestamp": datetime.now().isoformat()
        }
        
        for category in self.enterprise_categories:
            try:
                product_url = self.search_sku_in_category(sku, category)
                if product_url:
                    sku_result["found_in_categories"].append({
                        "category": category,
                        "product_url": product_url
                    })
                    
                    trusta_result = self.navigate_to_qvl_and_search_trusta(sku, product_url)
                    if trusta_result:
                        sku_result["qvl_accessible"] = True
                        if trusta_result.get("trusta_found"):
                            sku_result["trusta_found"] = True
                            sku_result["trusta_data"] = trusta_result
                            self.results["trusta_findings"].append(trusta_result)
                            print(f"🎉 TRUSTA FOUND for SKU {sku}!")
                            break  # Found TRUSTA, no need to search other categories
                
            except Exception as e:
                print(f"   ❌ Error searching {sku} in {category}: {e}")
                continue
        
        return sku_result
    
    def run_comprehensive_search(self):
        """Run comprehensive search across all SKUs"""
        print("🚀 Starting Comprehensive GIGABYTE SKU TRUSTA Search")
        print("=" * 70)
        
        if not self.setup_driver():
            return False
        
        skus = self.load_server_skus()
        if not skus:
            return False
        
        self.results["search_metadata"]["total_skus_searched"] = len(skus)
        
        try:
            for i, sku in enumerate(skus, 1):
                print(f"\n📊 Progress: {i}/{len(skus)} ({i/len(skus)*100:.1f}%)")
                
                sku_result = self.search_single_sku(sku)
                self.results["sku_results"][sku] = sku_result
                
                if sku_result["found_in_categories"]:
                    self.results["search_metadata"]["skus_found"] += 1
                if sku_result["qvl_accessible"]:
                    self.results["search_metadata"]["skus_with_qvl"] += 1
                if sku_result["trusta_found"]:
                    self.results["search_metadata"]["skus_with_trusta"] += 1
                
                time.sleep(2)
                
                if i % 10 == 0:
                    self.save_progress_report(f"progress_after_{i}_skus.json")
                    print(f"💾 Progress saved after {i} SKUs")
        
        except KeyboardInterrupt:
            print("\n⚠️ Search interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error during search: {e}")
        finally:
            if self.driver:
                self.driver.quit()
        
        self.results["search_metadata"]["end_time"] = datetime.now().isoformat()
        self.generate_search_summary()
        
        return True
    
    def generate_search_summary(self):
        """Generate comprehensive search summary"""
        metadata = self.results["search_metadata"]
        
        self.results["search_summary"] = {
            "total_skus_processed": metadata["total_skus_searched"],
            "skus_found_on_website": metadata["skus_found"],
            "skus_with_accessible_qvl": metadata["skus_with_qvl"],
            "skus_with_trusta_products": metadata["skus_with_trusta"],
            "success_rate": {
                "sku_discovery": f"{metadata['skus_found']/metadata['total_skus_searched']*100:.1f}%" if metadata['total_skus_searched'] > 0 else "0%",
                "qvl_access": f"{metadata['skus_with_qvl']/metadata['skus_found']*100:.1f}%" if metadata['skus_found'] > 0 else "0%",
                "trusta_discovery": f"{metadata['skus_with_trusta']/metadata['skus_with_qvl']*100:.1f}%" if metadata['skus_with_qvl'] > 0 else "0%"
            },
            "categories_searched": self.enterprise_categories,
            "total_trusta_findings": len(self.results["trusta_findings"])
        }
    
    def save_progress_report(self, filename):
        """Save progress report to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving progress report: {e}")
    
    def save_final_report(self):
        """Save final comprehensive report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gigabyte_comprehensive_sku_trusta_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 COMPREHENSIVE SEARCH COMPLETED")
            print("=" * 50)
            print(f"📁 Final report saved: {filename}")
            print(f"📈 Search Statistics:")
            print(f"   • Total SKUs searched: {self.results['search_metadata']['total_skus_searched']}")
            print(f"   • SKUs found on website: {self.results['search_metadata']['skus_found']}")
            print(f"   • SKUs with QVL access: {self.results['search_metadata']['skus_with_qvl']}")
            print(f"   • SKUs with TRUSTA: {self.results['search_metadata']['skus_with_trusta']}")
            print(f"   • Total TRUSTA findings: {len(self.results['trusta_findings'])}")
            
            if self.results['trusta_findings']:
                print(f"\n🎉 TRUSTA PRODUCTS FOUND:")
                for finding in self.results['trusta_findings']:
                    print(f"   • SKU: {finding['sku']}")
                    print(f"     URL: {finding['page_url']}")
                    if finding.get('matches'):
                        print(f"     Matches: {len(finding['matches'])}")
            
            return filename
            
        except Exception as e:
            print(f"❌ Error saving final report: {e}")
            return None

def main():
    """Main function"""
    crawler = GigabyteComprehensiveSKUCrawler()
    
    success = crawler.run_comprehensive_search()
    if success:
        report_file = crawler.save_final_report()
        if report_file:
            print(f"\n✅ Comprehensive search completed successfully!")
            print(f"📋 Report file: {report_file}")
            return 0
        else:
            print(f"\n⚠️ Search completed but report save failed")
            return 1
    else:
        print(f"\n❌ Comprehensive search failed")
        return 1

if __name__ == "__main__":
    exit(main())
