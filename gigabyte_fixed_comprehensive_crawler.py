#!/usr/bin/env python3
"""
Fixed Comprehensive GIGABYTE Server SKU TRUSTA Crawler
Systematically searches all server SKUs for TRUSTA products in QVL pages
Uses improved navigation logic based on successful browser testing
"""

import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class GigabyteFixedTrustaCrawler:
    def __init__(self):
        self.base_url = "https://www.gigabyte.com/Enterprise"
        self.categories = [
            "GPU-Server",
            "General-Purpose-Server", 
            "AI-Server",
            "High-Density-Server"
        ]
        self.driver = None
        self.results = {
            "search_metadata": {
                "start_time": datetime.now().isoformat(),
                "total_skus": 0,
                "skus_processed": 0,
                "skus_found": 0,
                "qvl_accessed": 0,
                "trusta_products_found": 0
            },
            "sku_results": [],
            "trusta_findings": [],
            "search_summary": {}
        }
        
    def setup_driver(self):
        """Initialize Chrome WebDriver with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def load_server_skus(self):
        """Load server SKUs from file"""
        try:
            with open('server-sku.txt', 'r', encoding='utf-8') as f:
                skus = [line.strip() for line in f if line.strip()]
            print(f"✅ Loaded {len(skus)} server SKUs")
            return skus
        except FileNotFoundError:
            print("❌ Error: server-sku.txt not found")
            return []
            
    def search_sku_in_category(self, sku, category):
        """Search for a specific SKU in a category"""
        category_url = f"{self.base_url}/{category}"
        
        try:
            print(f"   🔍 Searching in {category}...")
            self.driver.get(category_url)
            time.sleep(3)
            
            if "access denied" in self.driver.page_source.lower():
                print(f"   ❌ Access denied for {category}")
                return None
                
            page_source = self.driver.page_source.lower()
            sku_variations = [
                sku.lower(),
                sku.lower().replace('-000', ''),
                sku.lower().split('-')[0] if '-' in sku else sku.lower()
            ]
            
            for variation in sku_variations:
                if variation in page_source:
                    print(f"   ✅ Found SKU pattern '{variation}' in {category}")
                    
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        text = link.text or ""
                        
                        if any(var in href.lower() or var in text.lower() for var in sku_variations):
                            product_url = href
                            print(f"   🎯 Found product link: {product_url}")
                            return product_url
                            
            print(f"   ❌ SKU not found in {category}")
            return None
            
        except Exception as e:
            print(f"   ❌ Error searching {category}: {e}")
            return None
            
    def navigate_to_qvl_nvme(self, product_url):
        """Navigate to QVL NVMe SSD page for a product"""
        try:
            print(f"   📋 Accessing product page: {product_url}")
            self.driver.get(product_url)
            time.sleep(3)
            
            if "access denied" in self.driver.page_source.lower():
                print(f"   ❌ Access denied for product page")
                return None
                
            qvl_url = None
            
            if "/Enterprise/" in product_url:
                qvl_url = f"{product_url}/Support-QVL"
                print(f"   🔗 Constructed QVL URL: {qvl_url}")
            
            if not qvl_url:
                try:
                    qvl_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "QVL")
                    if not qvl_links:
                        qvl_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'QVL')]")
                    
                    if qvl_links:
                        qvl_url = qvl_links[0].get_attribute("href")
                        print(f"   🔗 Found QVL link: {qvl_url}")
                except:
                    pass
            
            if not qvl_url:
                print(f"   ❌ No QVL link found")
                return None
                
            print(f"   📋 Navigating to QVL page...")
            self.driver.get(qvl_url)
            time.sleep(3)
            
            nvme_url = f"{qvl_url}?CAT=Storage-NVMeSSD"
            print(f"   💾 Navigating to NVMe SSD section: {nvme_url}")
            self.driver.get(nvme_url)
            time.sleep(5)  # Give more time for table to load
            
            return nvme_url
            
        except Exception as e:
            print(f"   ❌ Error navigating to QVL: {e}")
            return None
            
    def extract_trusta_products(self, sku, qvl_url):
        """Extract TRUSTA products from QVL page"""
        try:
            print(f"   🔍 Searching for TRUSTA products...")
            
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            
            if "trusta" not in page_source and "t7p5" not in page_source:
                print(f"   ❌ No TRUSTA products found")
                return []
                
            print(f"   ✅ TRUSTA products detected!")
            
            trusta_products = []
            
            try:
                rows = self.driver.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    row_text = row.text.lower()
                    if "trusta" in row_text or "t7p5" in row_text:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 8:  # Ensure we have enough columns
                            product = {
                                "server_sku": sku,
                                "product_name": cells[0].text.strip(),
                                "vendor": cells[1].text.strip(),
                                "type": cells[2].text.strip(),
                                "form_factor": cells[3].text.strip(),
                                "interface": cells[4].text.strip(),
                                "capacity": cells[5].text.strip(),
                                "interface_speed": cells[6].text.strip(),
                                "series": cells[7].text.strip(),
                                "other": cells[8].text.strip() if len(cells) > 8 else "",
                                "remark": cells[9].text.strip() if len(cells) > 9 else "",
                                "qvl_url": qvl_url,
                                "found_timestamp": datetime.now().isoformat()
                            }
                            trusta_products.append(product)
                            print(f"   📦 Found: {product['product_name']} - {product['capacity']}")
                            
            except Exception as e:
                print(f"   ⚠️ Error extracting table data: {e}")
                if "t7p5-" in page_source:
                    trusta_matches = re.findall(r't7p5-[a-z0-9]+', page_source, re.IGNORECASE)
                    for match in trusta_matches:
                        product = {
                            "server_sku": sku,
                            "product_name": match.upper(),
                            "vendor": "TRUSTA",
                            "series": "T7P5 Series",
                            "qvl_url": qvl_url,
                            "found_timestamp": datetime.now().isoformat(),
                            "extraction_method": "regex_fallback"
                        }
                        trusta_products.append(product)
                        print(f"   📦 Found (fallback): {match.upper()}")
            
            return trusta_products
            
        except Exception as e:
            print(f"   ❌ Error extracting TRUSTA products: {e}")
            return []
            
    def search_single_sku(self, sku, sku_index, total_skus):
        """Search for TRUSTA products for a single SKU"""
        print(f"\n🔍 [{sku_index}/{total_skus}] Searching SKU: {sku}")
        
        sku_result = {
            "sku": sku,
            "search_timestamp": datetime.now().isoformat(),
            "found_in_category": None,
            "product_url": None,
            "qvl_url": None,
            "qvl_accessible": False,
            "trusta_products": [],
            "search_status": "not_found"
        }
        
        for category in self.categories:
            product_url = self.search_sku_in_category(sku, category)
            
            if product_url:
                sku_result["found_in_category"] = category
                sku_result["product_url"] = product_url
                sku_result["search_status"] = "found"
                self.results["search_metadata"]["skus_found"] += 1
                
                qvl_url = self.navigate_to_qvl_nvme(product_url)
                
                if qvl_url:
                    sku_result["qvl_url"] = qvl_url
                    sku_result["qvl_accessible"] = True
                    self.results["search_metadata"]["qvl_accessed"] += 1
                    
                    trusta_products = self.extract_trusta_products(sku, qvl_url)
                    
                    if trusta_products:
                        sku_result["trusta_products"] = trusta_products
                        sku_result["search_status"] = "trusta_found"
                        self.results["trusta_findings"].extend(trusta_products)
                        self.results["search_metadata"]["trusta_products_found"] += len(trusta_products)
                        print(f"   🎉 Found {len(trusta_products)} TRUSTA products!")
                
                break  # Found in this category, no need to search others
                
        self.results["sku_results"].append(sku_result)
        self.results["search_metadata"]["skus_processed"] += 1
        
        if sku_index % 10 == 0:
            self.save_progress_report(f"progress_after_{sku_index}_skus.json")
            
        return sku_result
        
    def save_progress_report(self, filename):
        """Save progress report"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"💾 Progress saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving progress: {e}")
            
    def generate_final_report(self):
        """Generate final comprehensive report"""
        self.results["search_metadata"]["end_time"] = datetime.now().isoformat()
        self.results["search_metadata"]["total_skus"] = len(self.results["sku_results"])
        
        summary = {
            "total_skus_searched": self.results["search_metadata"]["skus_processed"],
            "skus_found_on_website": self.results["search_metadata"]["skus_found"],
            "skus_with_qvl_access": self.results["search_metadata"]["qvl_accessed"],
            "skus_with_trusta_products": len([r for r in self.results["sku_results"] if r["trusta_products"]]),
            "total_trusta_products": self.results["search_metadata"]["trusta_products_found"],
            "category_breakdown": {},
            "trusta_product_summary": []
        }
        
        for category in self.categories:
            count = len([r for r in self.results["sku_results"] if r["found_in_category"] == category])
            summary["category_breakdown"][category] = count
            
        for product in self.results["trusta_findings"]:
            summary["trusta_product_summary"].append({
                "server_sku": product["server_sku"],
                "product_name": product["product_name"],
                "capacity": product.get("capacity", ""),
                "series": product.get("series", "")
            })
            
        self.results["search_summary"] = summary
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gigabyte_comprehensive_sku_trusta_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"📊 Final report saved to {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving final report: {e}")
            return None
            
    def run_comprehensive_search(self):
        """Run comprehensive search for all server SKUs"""
        print("🚀 Starting Fixed Comprehensive GIGABYTE TRUSTA Search")
        print("=" * 60)
        
        server_skus = self.load_server_skus()
        if not server_skus:
            return None
            
        self.results["search_metadata"]["total_skus"] = len(server_skus)
        
        try:
            self.setup_driver()
            print(f"✅ Chrome WebDriver initialized")
        except Exception as e:
            print(f"❌ Error setting up WebDriver: {e}")
            return None
            
        try:
            for i, sku in enumerate(server_skus, 1):
                try:
                    self.search_single_sku(sku, i, len(server_skus))
                    
                    time.sleep(2)
                    
                except KeyboardInterrupt:
                    print(f"\n⏹️ Search interrupted by user")
                    break
                except Exception as e:
                    print(f"❌ Error searching SKU {sku}: {e}")
                    continue
                    
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 WebDriver closed")
                
        report_file = self.generate_final_report()
        
        self.display_search_summary()
        
        return report_file
        
    def display_search_summary(self):
        """Display search summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE SEARCH SUMMARY")
        print("=" * 60)
        
        summary = self.results["search_summary"]
        
        print(f"🔍 Total SKUs Searched: {summary['total_skus_searched']}")
        print(f"✅ SKUs Found on Website: {summary['skus_found_on_website']}")
        print(f"📋 SKUs with QVL Access: {summary['skus_with_qvl_access']}")
        print(f"🎯 SKUs with TRUSTA Products: {summary['skus_with_trusta_products']}")
        print(f"📦 Total TRUSTA Products Found: {summary['total_trusta_products']}")
        
        print(f"\n📂 Category Breakdown:")
        for category, count in summary["category_breakdown"].items():
            print(f"   • {category}: {count} SKUs")
            
        if summary["trusta_product_summary"]:
            print(f"\n🎉 TRUSTA Products Found:")
            for product in summary["trusta_product_summary"]:
                print(f"   • {product['server_sku']}: {product['product_name']} ({product.get('capacity', 'N/A')})")
        else:
            print(f"\n❌ No TRUSTA products found in any server QVL")
            
        print("=" * 60)

def main():
    """Main function"""
    crawler = GigabyteFixedTrustaCrawler()
    report_file = crawler.run_comprehensive_search()
    
    if report_file:
        print(f"\n🎯 MISSION ACCOMPLISHED!")
        print(f"📁 Comprehensive report saved: {report_file}")
        print(f"📊 Ready to generate Excel spreadsheet from results")
        return 0
    else:
        print(f"\n❌ Search failed")
        return 1

if __name__ == "__main__":
    exit(main())
