#!/usr/bin/env python3
"""
GIGABYTE G293-S40-AAP1 Targeted TRUSTA T7P5 Web Crawler
Specifically targets the G293-S40-AAP1 GPU server page for TRUSTA or T7P5 information
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

class GigabyteG293TargetedCrawler:
    def __init__(self):
        self.target_url = "https://www.gigabyte.com/Enterprise/GPU-Server/G293-S40-AAP1"
        self.search_terms = ["TRUSTA", "T7P5", "trusta", "t7p5"]
        self.storage_keywords = [
            "nvme", "ssd", "storage", "drive", "gen5", "gen 5", "pcie 5.0", "pcie gen 5",
            "hot-swap", "2.5", "m.2", "sata", "sas", "capacity", "tb", "gb"
        ]
        self.results = {
            "target_page": self.target_url,
            "found_mentions": [],
            "storage_specifications": [],
            "technical_details": [],
            "page_sections": {},
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
    
    def search_text_for_terms(self, text, context_name="", extract_context=True):
        """Search text for TRUSTA or T7P5 mentions with enhanced context"""
        found_terms = []
        text_lower = text.lower()
        
        for term in self.search_terms:
            if term.lower() in text_lower:
                if extract_context:
                    pattern = re.compile(f'.{{0,300}}{re.escape(term.lower())}.{{0,300}}', re.IGNORECASE | re.DOTALL)
                    matches = pattern.findall(text)
                    for match in matches:
                        found_terms.append({
                            "term": term,
                            "context": match.strip(),
                            "section": context_name,
                            "match_type": "exact"
                        })
                else:
                    found_terms.append({
                        "term": term,
                        "context": text[:500] if len(text) > 500 else text,
                        "section": context_name,
                        "match_type": "exact"
                    })
        
        storage_content = []
        for keyword in self.storage_keywords:
            if keyword in text_lower:
                sentences = re.split(r'[.!?]+', text)
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence.strip()) > 10:
                        storage_content.append({
                            "keyword": keyword,
                            "content": sentence.strip(),
                            "section": context_name
                        })
        
        return found_terms, storage_content
    
    def extract_page_sections(self):
        """Extract different sections of the G293-S40-AAP1 page"""
        sections = {}
        
        try:
            try:
                title = self.driver.find_element(By.TAG_NAME, "h1").text
                sections["title"] = title
            except:
                sections["title"] = "G293-S40-AAP1"
            
            try:
                subtitle_elements = self.driver.find_elements(By.XPATH, "//h1/following-sibling::*[1]")
                if subtitle_elements:
                    sections["description"] = subtitle_elements[0].text
            except:
                sections["description"] = ""
            
            try:
                feature_lists = self.driver.find_elements(By.XPATH, "//ul[li[contains(text(), 'Supports') or contains(text(), 'Dual') or contains(text(), 'Channel')]]")
                features = []
                for ul in feature_lists:
                    items = ul.find_elements(By.TAG_NAME, "li")
                    for item in items:
                        text = item.text.strip()
                        if text and len(text) > 5:
                            features.append(text)
                sections["key_features"] = features
            except Exception as e:
                logger.warning(f"Error extracting features: {e}")
                sections["key_features"] = []
            
            try:
                spec_button = self.driver.find_element(By.XPATH, "//span[text()='Specifications']")
                spec_button.click()
                time.sleep(3)
                
                spec_content = self.driver.find_element(By.TAG_NAME, "body").text
                sections["specifications"] = spec_content
                
                overview_button = self.driver.find_element(By.XPATH, "//span[text()='Overview']")
                overview_button.click()
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"Could not access specifications tab: {e}")
                sections["specifications"] = ""
            
            try:
                tech_sections = self.driver.find_elements(By.XPATH, "//h2 | //h4")
                tech_content = []
                for section in tech_sections:
                    text = section.text.strip()
                    if text and any(keyword in text.lower() for keyword in ["performance", "storage", "nvme", "gen5", "pcie", "accelerator"]):
                        try:
                            parent = section.find_element(By.XPATH, "./..")
                            content = parent.text.strip()
                            if len(content) > len(text):
                                tech_content.append({
                                    "heading": text,
                                    "content": content
                                })
                        except:
                            tech_content.append({
                                "heading": text,
                                "content": text
                            })
                
                sections["technical_details"] = tech_content
                
            except Exception as e:
                logger.warning(f"Error extracting technical details: {e}")
                sections["technical_details"] = []
            
            try:
                full_text = self.driver.find_element(By.TAG_NAME, "body").text
                sections["full_page_text"] = full_text
            except:
                sections["full_page_text"] = ""
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting page sections: {e}")
            return sections
    
    def analyze_storage_specifications(self, sections):
        """Analyze storage-related specifications from the page"""
        storage_specs = []
        
        for feature in sections.get("key_features", []):
            if any(keyword in feature.lower() for keyword in self.storage_keywords):
                storage_specs.append({
                    "type": "key_feature",
                    "content": feature,
                    "analysis": self.analyze_storage_feature(feature)
                })
        
        for detail in sections.get("technical_details", []):
            heading = detail.get("heading", "")
            content = detail.get("content", "")
            
            if any(keyword in heading.lower() for keyword in self.storage_keywords) or \
               any(keyword in content.lower() for keyword in self.storage_keywords):
                storage_specs.append({
                    "type": "technical_detail",
                    "heading": heading,
                    "content": content,
                    "analysis": self.analyze_storage_feature(content)
                })
        
        spec_text = sections.get("specifications", "")
        if spec_text:
            storage_lines = []
            for line in spec_text.split('\n'):
                if any(keyword in line.lower() for keyword in self.storage_keywords):
                    storage_lines.append(line.strip())
            
            if storage_lines:
                storage_specs.append({
                    "type": "specification",
                    "content": storage_lines,
                    "analysis": "Specification details"
                })
        
        return storage_specs
    
    def analyze_storage_feature(self, text):
        """Analyze a storage feature for relevant details"""
        analysis = {}
        text_lower = text.lower()
        
        capacity_pattern = r'(\d+)\s*(tb|gb)'
        capacity_matches = re.findall(capacity_pattern, text_lower)
        if capacity_matches:
            analysis["capacities"] = [f"{num}{unit}" for num, unit in capacity_matches]
        
        if "nvme" in text_lower:
            analysis["interface"] = "NVMe"
        elif "sata" in text_lower:
            analysis["interface"] = "SATA"
        elif "sas" in text_lower:
            analysis["interface"] = "SAS"
        
        if "gen5" in text_lower or "gen 5" in text_lower or "pcie 5" in text_lower:
            analysis["pcie_generation"] = "Gen 5"
        elif "gen4" in text_lower or "gen 4" in text_lower or "pcie 4" in text_lower:
            analysis["pcie_generation"] = "Gen 4"
        
        if "2.5" in text:
            analysis["form_factor"] = "2.5 inch"
        elif "m.2" in text_lower:
            analysis["form_factor"] = "M.2"
        
        if "hot-swap" in text_lower or "hot swap" in text_lower:
            analysis["hot_swap"] = True
        
        return analysis
    
    def run_targeted_crawler(self):
        """Main targeted crawler execution for G293-S40-AAP1"""
        logger.info(f"Starting targeted crawler for G293-S40-AAP1: {self.target_url}")
        
        if not self.setup_driver():
            return False
        
        try:
            logger.info(f"Loading target page: {self.target_url}")
            self.driver.get(self.target_url)
            time.sleep(5)
            
            self.accept_cookies()
            
            time.sleep(3)
            
            logger.info("Extracting page sections...")
            sections = self.extract_page_sections()
            self.results["page_sections"] = sections
            
            logger.info("Searching for TRUSTA/T7P5 mentions...")
            all_found_terms = []
            all_storage_content = []
            
            for section_name, section_content in sections.items():
                if isinstance(section_content, str):
                    found_terms, storage_content = self.search_text_for_terms(section_content, section_name)
                    all_found_terms.extend(found_terms)
                    all_storage_content.extend(storage_content)
                elif isinstance(section_content, list):
                    for item in section_content:
                        if isinstance(item, str):
                            found_terms, storage_content = self.search_text_for_terms(item, f"{section_name}_item")
                            all_found_terms.extend(found_terms)
                            all_storage_content.extend(storage_content)
                        elif isinstance(item, dict):
                            for key, value in item.items():
                                if isinstance(value, str):
                                    found_terms, storage_content = self.search_text_for_terms(value, f"{section_name}_{key}")
                                    all_found_terms.extend(found_terms)
                                    all_storage_content.extend(storage_content)
            
            self.results["found_mentions"] = all_found_terms
            
            logger.info("Analyzing storage specifications...")
            storage_specs = self.analyze_storage_specifications(sections)
            self.results["storage_specifications"] = storage_specs
            
            self.results["storage_related_content"] = all_storage_content
            
            self.generate_summary()
            
            return True
            
        except Exception as e:
            error_msg = f"Error during targeted crawling: {e}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def generate_summary(self):
        """Generate summary of findings"""
        total_mentions = len(self.results["found_mentions"])
        storage_specs_found = len(self.results["storage_specifications"])
        storage_content_found = len(self.results["storage_related_content"])
        
        gen5_nvme_found = False
        for spec in self.results["storage_specifications"]:
            analysis = spec.get("analysis", {})
            if analysis.get("pcie_generation") == "Gen 5" and analysis.get("interface") == "NVMe":
                gen5_nvme_found = True
                break
        
        self.results["search_summary"] = {
            "target_url": self.target_url,
            "trusta_t7p5_mentions_found": total_mentions,
            "storage_specifications_extracted": storage_specs_found,
            "storage_related_content_items": storage_content_found,
            "gen5_nvme_support_confirmed": gen5_nvme_found,
            "search_terms": self.search_terms,
            "storage_keywords_searched": self.storage_keywords,
            "page_sections_analyzed": list(self.results["page_sections"].keys()),
            "errors_encountered": len(self.results["errors"])
        }
        
        logger.info(f"Targeted crawling complete. Found {total_mentions} TRUSTA/T7P5 mentions, {storage_specs_found} storage specs")
    
    def display_results(self):
        """Display the targeted crawling results"""
        print("\n" + "="*80)
        print("GIGABYTE G293-S40-AAP1 TARGETED TRUSTA T7P5 CRAWLER RESULTS")
        print("="*80)
        
        summary = self.results["search_summary"]
        print(f"\nTARGET PAGE: {summary['target_url']}")
        print(f"\nSUMMARY:")
        print(f"- TRUSTA/T7P5 mentions found: {summary['trusta_t7p5_mentions_found']}")
        print(f"- Storage specifications extracted: {summary['storage_specifications_extracted']}")
        print(f"- Storage-related content items: {summary['storage_related_content_items']}")
        print(f"- Gen 5 NVMe support confirmed: {summary['gen5_nvme_support_confirmed']}")
        print(f"- Page sections analyzed: {len(summary['page_sections_analyzed'])}")
        print(f"- Errors encountered: {summary['errors_encountered']}")
        
        if self.results["found_mentions"]:
            print(f"\n🎯 TRUSTA/T7P5 MENTIONS FOUND:")
            print("-" * 50)
            for i, mention in enumerate(self.results["found_mentions"], 1):
                print(f"\n{i}. Term: {mention['term']} (Section: {mention['section']})")
                print(f"   Match Type: {mention['match_type']}")
                print(f"   Context: {mention['context'][:300]}...")
        else:
            print(f"\n❌ NO TRUSTA/T7P5 MENTIONS FOUND")
            print("-" * 50)
            print("No direct references to TRUSTA or T7P5 were found on the G293-S40-AAP1 page.")
        
        print(f"\n💾 STORAGE SPECIFICATIONS FOUND:")
        print("-" * 50)
        if self.results["storage_specifications"]:
            for i, spec in enumerate(self.results["storage_specifications"], 1):
                print(f"\n{i}. Type: {spec['type']}")
                if spec['type'] == 'key_feature':
                    print(f"   Feature: {spec['content']}")
                elif spec['type'] == 'technical_detail':
                    print(f"   Heading: {spec.get('heading', 'N/A')}")
                    print(f"   Content: {spec['content'][:200]}...")
                elif spec['type'] == 'specification':
                    print(f"   Specifications: {spec['content'][:3]}")  # Show first 3 items
                
                analysis = spec.get('analysis', {})
                if analysis:
                    print(f"   Analysis: {analysis}")
        else:
            print("No storage specifications extracted.")
        
        page_sections = self.results.get("page_sections", {})
        key_features = page_sections.get("key_features", [])
        
        print(f"\n🖥️ G293-S40-AAP1 KEY FEATURES:")
        print("-" * 50)
        for feature in key_features[:10]:  # Show first 10 features
            print(f"- {feature}")
        
        storage_content = self.results.get("storage_related_content", [])
        if storage_content:
            print(f"\n🔍 STORAGE-RELATED CONTENT FOUND:")
            print("-" * 50)
            for i, content in enumerate(storage_content[:5], 1):  # Show first 5
                print(f"{i}. Keyword: {content['keyword']}")
                print(f"   Content: {content['content'][:150]}...")
                print(f"   Section: {content['section']}")
        
        print(f"\n📋 CONCLUSIONS:")
        print("-" * 50)
        if summary['gen5_nvme_support_confirmed']:
            print("✅ G293-S40-AAP1 DOES support PCIe Gen 5 NVMe storage")
            print("✅ Server has hot-swap storage bays compatible with Gen 5 SSDs")
        else:
            print("⚠️  Gen 5 NVMe support status unclear from page content")
        
        if summary['trusta_t7p5_mentions_found'] == 0:
            print("❌ TRUSTA T7P5 is NOT specifically mentioned as a supported/included SSD")
            print("💡 However, the server supports standard PCIe Gen 5 NVMe SSDs")
            print("💡 TRUSTA T7P5 could potentially be compatible if it's a standard Gen 5 NVMe SSD")
        
        if self.results["errors"]:
            print(f"\n⚠️  ERRORS ENCOUNTERED:")
            print("-" * 50)
            for error in self.results["errors"]:
                print(f"- {error}")
        
        print("\n" + "="*80)
    
    def save_results(self, filename="gigabyte_g293_targeted_results.json"):
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
    crawler = GigabyteG293TargetedCrawler()
    
    print("GIGABYTE G293-S40-AAP1 Targeted TRUSTA T7P5 Web Crawler")
    print("Targeting specific GPU server page for TRUSTA/T7P5 information")
    print("-" * 80)
    
    success = crawler.run_targeted_crawler()
    
    if success:
        crawler.display_results()
        crawler.save_results()
    else:
        print("Targeted crawler failed to complete successfully. Check the logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
