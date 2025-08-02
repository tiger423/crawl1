#!/usr/bin/env python3
"""
GIGABYTE G293-S40-AAP1 QVL TRUSTA T7P5 Web Crawler
Specifically targets the QVL (Qualified Vendor List) NVMe SSD section for TRUSTA T7P5 information
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

class GigabyteQVLTrustaCrawler:
    def __init__(self):
        self.base_url = "https://www.gigabyte.com/Enterprise/GPU-Server/G293-S40-AAP1"
        self.qvl_url = "https://www.gigabyte.com/Enterprise/GPU-Server/G293-S40-AAP1/Support-QVL"
        self.nvme_qvl_url = "https://www.gigabyte.com/Enterprise/GPU-Server/G293-S40-AAP1/Support-QVL?CAT=Storage-NVMeSSD"
        self.search_terms = ["TRUSTA", "T7P5", "trusta", "t7p5"]
        self.results = {
            "target_server": "G293-S40-AAP1",
            "qvl_url": self.nvme_qvl_url,
            "trusta_products_found": [],
            "all_nvme_products": [],
            "qvl_summary": {},
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
    
    def navigate_to_qvl_nvme(self):
        """Navigate to the QVL NVMe SSD page"""
        try:
            logger.info(f"Loading QVL NVMe SSD page: {self.nvme_qvl_url}")
            self.driver.get(self.nvme_qvl_url)
            time.sleep(5)
            
            self.accept_cookies()
            
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            time.sleep(5)
            
            logger.info("Successfully loaded QVL NVMe SSD page")
            return True
            
        except Exception as e:
            error_msg = f"Error navigating to QVL NVMe page: {e}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return False
    
    def extract_qvl_table_data(self):
        """Extract all NVMe SSD data from the QVL table"""
        try:
            table = self.driver.find_element(By.XPATH, "//table[.//th[text()='Product Name']]")
            
            headers = []
            header_row = table.find_element(By.TAG_NAME, "thead").find_element(By.TAG_NAME, "tr")
            for th in header_row.find_elements(By.TAG_NAME, "th"):
                headers.append(th.text.strip())
            
            logger.info(f"Found table headers: {headers}")
            
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            all_products = []
            trusta_products = []
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) < len(headers) or not cells[0].text.strip():
                    continue
                
                product_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        product_data[headers[i]] = cell.text.strip()
                
                if not product_data.get("Product Name"):
                    continue
                
                all_products.append(product_data)
                
                vendor = product_data.get("Vendor", "").upper()
                product_name = product_data.get("Product Name", "").upper()
                series = product_data.get("Series", "").upper()
                
                if ("TRUSTA" in vendor or "TRUSTA" in product_name or 
                    "T7P5" in product_name or "T7P5" in series):
                    
                    product_data["analysis"] = self.analyze_trusta_product(product_data)
                    trusta_products.append(product_data)
                    logger.info(f"Found TRUSTA product: {product_data.get('Product Name')}")
            
            self.results["all_nvme_products"] = all_products
            self.results["trusta_products_found"] = trusta_products
            
            logger.info(f"Extracted {len(all_products)} total NVMe products, {len(trusta_products)} TRUSTA products")
            return True
            
        except Exception as e:
            error_msg = f"Error extracting QVL table data: {e}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return False
    
    def analyze_trusta_product(self, product_data):
        """Analyze TRUSTA product specifications"""
        analysis = {
            "is_gen5": False,
            "is_nvme": False,
            "form_factor_type": "",
            "capacity_tb": 0,
            "interface_details": "",
            "vroc_support": False
        }
        
        interface_speed = product_data.get("Interface Speed", "").lower()
        if "gen5" in interface_speed or "gen 5" in interface_speed:
            analysis["is_gen5"] = True
        
        interface = product_data.get("Interface", "").lower()
        if "nvme" in interface:
            analysis["is_nvme"] = True
        
        form_factor = product_data.get("Form Factor", "")
        analysis["form_factor_type"] = form_factor
        
        capacity = product_data.get("Capacity", "")
        if "TB" in capacity.upper():
            try:
                capacity_num = float(re.findall(r'(\d+\.?\d*)', capacity)[0])
                analysis["capacity_tb"] = capacity_num
            except:
                pass
        elif "GB" in capacity.upper():
            try:
                capacity_num = float(re.findall(r'(\d+\.?\d*)', capacity)[0])
                analysis["capacity_tb"] = capacity_num / 1000  # Convert GB to TB
            except:
                pass
        
        other = product_data.get("Other", "").lower()
        remark = product_data.get("Remark", "").lower()
        if "vroc" in other or "vroc" in remark:
            analysis["vroc_support"] = True
        
        analysis["interface_details"] = f"{product_data.get('Interface', '')} - {product_data.get('Interface Speed', '')}"
        
        return analysis
    
    def generate_qvl_summary(self):
        """Generate summary of QVL findings"""
        total_products = len(self.results["all_nvme_products"])
        trusta_count = len(self.results["trusta_products_found"])
        
        gen5_count = 0
        total_capacity = 0
        capacity_options = []
        
        for product in self.results["trusta_products_found"]:
            analysis = product.get("analysis", {})
            if analysis.get("is_gen5"):
                gen5_count += 1
            
            capacity = analysis.get("capacity_tb", 0)
            if capacity > 0:
                total_capacity += capacity
                capacity_options.append(f"{capacity}TB")
        
        vendor_counts = {}
        for product in self.results["all_nvme_products"]:
            vendor = product.get("Vendor", "Unknown")
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
        
        self.results["qvl_summary"] = {
            "total_nvme_products_in_qvl": total_products,
            "trusta_products_found": trusta_count,
            "trusta_gen5_products": gen5_count,
            "trusta_capacity_options": sorted(list(set(capacity_options))),
            "total_trusta_capacity_tb": total_capacity,
            "vendor_distribution": vendor_counts,
            "qvl_page_url": self.nvme_qvl_url
        }
        
        self.results["search_summary"] = {
            "search_successful": trusta_count > 0,
            "search_terms_used": self.search_terms,
            "qvl_section_accessed": "Storage - NVMe SSD",
            "target_server_model": "G293-S40-AAP1",
            "findings": f"Found {trusta_count} TRUSTA T7P5 products in QVL"
        }
        
        logger.info(f"Generated QVL summary: {trusta_count} TRUSTA products found")
    
    def run_qvl_crawler(self):
        """Main QVL crawler execution"""
        logger.info("Starting GIGABYTE G293-S40-AAP1 QVL TRUSTA T7P5 crawler")
        
        if not self.setup_driver():
            return False
        
        try:
            if not self.navigate_to_qvl_nvme():
                return False
            
            if not self.extract_qvl_table_data():
                return False
            
            self.generate_qvl_summary()
            
            return True
            
        except Exception as e:
            error_msg = f"Error during QVL crawling: {e}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def display_results(self):
        """Display the QVL crawling results"""
        print("\n" + "="*80)
        print("GIGABYTE G293-S40-AAP1 QVL TRUSTA T7P5 CRAWLER RESULTS")
        print("="*80)
        
        qvl_summary = self.results["qvl_summary"]
        search_summary = self.results["search_summary"]
        
        print(f"\nTARGET SERVER: {self.results['target_server']}")
        print(f"QVL URL: {self.results['qvl_url']}")
        print(f"\nQVL SUMMARY:")
        print(f"- Total NVMe products in QVL: {qvl_summary['total_nvme_products_in_qvl']}")
        print(f"- TRUSTA products found: {qvl_summary['trusta_products_found']}")
        print(f"- TRUSTA Gen 5 products: {qvl_summary['trusta_gen5_products']}")
        print(f"- Search successful: {search_summary['search_successful']}")
        
        if self.results["trusta_products_found"]:
            print(f"\n🎯 TRUSTA T7P5 PRODUCTS FOUND IN QVL:")
            print("-" * 60)
            for i, product in enumerate(self.results["trusta_products_found"], 1):
                print(f"\n{i}. Product: {product.get('Product Name', 'N/A')}")
                print(f"   Vendor: {product.get('Vendor', 'N/A')}")
                print(f"   Capacity: {product.get('Capacity', 'N/A')}")
                print(f"   Interface: {product.get('Interface', 'N/A')}")
                print(f"   Interface Speed: {product.get('Interface Speed', 'N/A')}")
                print(f"   Form Factor: {product.get('Form Factor', 'N/A')}")
                print(f"   Series: {product.get('Series', 'N/A')}")
                print(f"   Type: {product.get('Type', 'N/A')}")
                
                analysis = product.get("analysis", {})
                if analysis:
                    print(f"   Analysis:")
                    print(f"     - PCIe Gen 5: {analysis.get('is_gen5', False)}")
                    print(f"     - NVMe Interface: {analysis.get('is_nvme', False)}")
                    print(f"     - Capacity (TB): {analysis.get('capacity_tb', 0)}")
                    print(f"     - VROC Support: {analysis.get('vroc_support', False)}")
                
                other = product.get('Other', '')
                remark = product.get('Remark', '')
                if other:
                    print(f"   Other: {other}")
                if remark:
                    print(f"   Remark: {remark}")
        else:
            print(f"\n❌ NO TRUSTA T7P5 PRODUCTS FOUND IN QVL")
        
        print(f"\n📊 CAPACITY OPTIONS AVAILABLE:")
        print("-" * 40)
        capacity_options = qvl_summary.get('trusta_capacity_options', [])
        if capacity_options:
            for capacity in capacity_options:
                print(f"- {capacity}")
        else:
            print("No capacity information available")
        
        print(f"\n🏭 VENDOR DISTRIBUTION IN QVL (Top 10):")
        print("-" * 50)
        vendor_dist = qvl_summary.get('vendor_distribution', {})
        sorted_vendors = sorted(vendor_dist.items(), key=lambda x: x[1], reverse=True)
        for vendor, count in sorted_vendors[:10]:
            print(f"- {vendor}: {count} products")
        
        print(f"\n✅ KEY FINDINGS:")
        print("-" * 30)
        if qvl_summary['trusta_products_found'] > 0:
            print(f"✅ TRUSTA T7P5 products ARE officially supported in G293-S40-AAP1 QVL")
            print(f"✅ Found {qvl_summary['trusta_products_found']} TRUSTA products in the QVL")
            print(f"✅ {qvl_summary['trusta_gen5_products']} of them are PCIe Gen 5 products")
            print(f"✅ Available in {len(capacity_options)} different capacity options")
            print(f"✅ Total combined capacity: {qvl_summary['total_trusta_capacity_tb']}TB")
        else:
            print(f"❌ No TRUSTA T7P5 products found in QVL")
        
        if self.results["errors"]:
            print(f"\n⚠️  ERRORS ENCOUNTERED:")
            print("-" * 40)
            for error in self.results["errors"]:
                print(f"- {error}")
        
        print("\n" + "="*80)
    
    def save_results(self, filename="gigabyte_qvl_trusta_results.json"):
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
    crawler = GigabyteQVLTrustaCrawler()
    
    print("GIGABYTE G293-S40-AAP1 QVL TRUSTA T7P5 Web Crawler")
    print("Targeting QVL (Qualified Vendor List) NVMe SSD section for TRUSTA/T7P5 information")
    print("-" * 80)
    
    success = crawler.run_qvl_crawler()
    
    if success:
        crawler.display_results()
        crawler.save_results()
    else:
        print("QVL crawler failed to complete successfully. Check the logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
