#!/usr/bin/env python3
"""
Smart Targeted GIGABYTE Server SKU TRUSTA Crawler
Uses known working URL patterns and focuses on likely matches first
More efficient approach based on successful browser navigation
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

class GigabyteSmartCrawler:
    def __init__(self):
        self.base_url = "https://www.gigabyte.com/Enterprise"
        self.categories = [
            "GPU-Server",
            "AI-Server", 
            "General-Purpose-Server",
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
                "trusta_products_found": 0,
                "successful_urls": []
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
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(3)
        
    def load_server_skus(self):
        """Load server SKUs from file and prioritize likely matches"""
        try:
            with open('server-sku.txt', 'r', encoding='utf-8') as f:
                all_skus = [line.strip() for line in f if line.strip()]
            
            priority_skus = []
            regular_skus = []
            
            for sku in all_skus:
                if sku.startswith('G293'):
                    priority_skus.append(sku)
                else:
                    regular_skus.append(sku)
            
            ordered_skus = priority_skus + regular_skus
            print(f"✅ Loaded {len(ordered_skus)} server SKUs ({len(priority_skus)} prioritized)")
            return ordered_skus
        except FileNotFoundError:
            print("❌ Error: server-sku.txt not found")
            return []
            
    def test_direct_qvl_url(self, sku, category):
        """Test direct QVL URL construction"""
        base_sku = sku.replace('-000', '') if sku.endswith('-000') else sku
        qvl_url = f"{self.base_url}/{category}/{base_sku}/Support-QVL?CAT=Storage-NVMeSSD"
        
        try:
            print(f"   🔗 Testing direct QVL: {qvl_url}")
            self.driver.get(qvl_url)
            time.sleep(4)  # Give time for page to load
            
            page_source = self.driver.page_source.lower()
            title = self.driver.title.lower()
            
            if any(error in page_source for error in ["access denied", "404", "not found", "error"]):
                print(f"   ❌ Error page detected")
                return None
                
            if any(error in title for error in ["404", "not found", "error"]):
                print(f"   ❌ Error in title")
                return None
                
            if any(indicator in page_source for indicator in ["nvme ssd", "storage", "qvl", "qualified"]):
                print(f"   ✅ Valid QVL page found")
                self.results["search_metadata"]["successful_urls"].append(qvl_url)
                return qvl_url
            else:
                print(f"   ⚠️ Page loaded but doesn't look like QVL")
                return None
                
        except Exception as e:
            print(f"   ❌ Error accessing QVL URL: {e}")
            return None
            
    def extract_trusta_products_from_qvl(self, sku, qvl_url):
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
                        if len(cells) >= 6:  # Ensure we have enough columns
                            product = {
                                "server_sku": sku,
                                "product_name": cells[0].text.strip() if len(cells) > 0 else "",
                                "vendor": cells[1].text.strip() if len(cells) > 1 else "",
                                "type": cells[2].text.strip() if len(cells) > 2 else "",
                                "form_factor": cells[3].text.strip() if len(cells) > 3 else "",
                                "interface": cells[4].text.strip() if len(cells) > 4 else "",
                                "capacity": cells[5].text.strip() if len(cells) > 5 else "",
                                "interface_speed": cells[6].text.strip() if len(cells) > 6 else "",
                                "series": cells[7].text.strip() if len(cells) > 7 else "",
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
            "qvl_url": None,
            "qvl_accessible": False,
            "trusta_products": [],
            "search_status": "not_found"
        }
        
        for category in self.categories:
            qvl_url = self.test_direct_qvl_url(sku, category)
            
            if qvl_url:
                sku_result["found_in_category"] = category
                sku_result["qvl_url"] = qvl_url
                sku_result["qvl_accessible"] = True
                sku_result["search_status"] = "found"
                self.results["search_metadata"]["skus_found"] += 1
                self.results["search_metadata"]["qvl_accessed"] += 1
                
                trusta_products = self.extract_trusta_products_from_qvl(sku, qvl_url)
                
                if trusta_products:
                    sku_result["trusta_products"] = trusta_products
                    sku_result["search_status"] = "trusta_found"
                    self.results["trusta_findings"].extend(trusta_products)
                    self.results["search_metadata"]["trusta_products_found"] += len(trusta_products)
                    print(f"   🎉 Found {len(trusta_products)} TRUSTA products!")
                
                break  # Found in this category, no need to test others
                
        self.results["sku_results"].append(sku_result)
        self.results["search_metadata"]["skus_processed"] += 1
        
        if sku_index % 25 == 0:
            self.save_progress_report(f"smart_progress_after_{sku_index}_skus.json")
            
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
            "trusta_product_summary": [],
            "successful_urls": self.results["search_metadata"]["successful_urls"]
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
        filename = f"gigabyte_smart_trusta_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"📊 Final report saved to {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving final report: {e}")
            return None
            
    def run_smart_search(self):
        """Run smart search for server SKUs"""
        print("🚀 Starting Smart Targeted GIGABYTE TRUSTA Search")
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
                    
                    time.sleep(1)
                    
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
        print("📊 SMART SEARCH SUMMARY")
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
            
        if summary["successful_urls"]:
            print(f"\n🔗 Successful QVL URLs ({len(summary['successful_urls'])}):")
            for url in summary["successful_urls"][:5]:  # Show first 5
                print(f"   • {url}")
            if len(summary["successful_urls"]) > 5:
                print(f"   ... and {len(summary['successful_urls']) - 5} more")
            
        print("=" * 60)

def main():
    """Main function"""
    crawler = GigabyteSmartCrawler()
    report_file = crawler.run_smart_search()
    
    if report_file:
        print(f"\n🎯 SMART SEARCH COMPLETED!")
        print(f"📁 Comprehensive report saved: {report_file}")
        print(f"📊 Ready to generate Excel spreadsheet from results")
        return 0
    else:
        print(f"\n❌ Search failed")
        return 1

if __name__ == "__main__":
    exit(main())
