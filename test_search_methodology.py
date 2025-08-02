#!/usr/bin/env python3
"""
Test Search Methodology for Known Working SKU
Quick test to verify our search approach works for G293-S40-AAP1
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_g293_search():
    """Test search for G293-S40-AAP1 which we know exists"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🔍 Testing search methodology for G293-S40-AAP1")
        
        print("\n📋 Test 1: Direct URL approach")
        direct_url = "https://www.gigabyte.com/Enterprise/GPU-Server/G293-S40-AAP1"
        driver.get(direct_url)
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        print(f"   ✅ Direct URL accessible: {direct_url}")
        print(f"   📄 Page title: {driver.title}")
        
        print("\n📋 Test 2: Search in GPU-Server category")
        category_url = "https://www.gigabyte.com/Enterprise/GPU-Server"
        driver.get(category_url)
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        
        search_patterns = [
            "g293-s40-aap1-000",  # Full SKU
            "g293-s40-aap1",      # Without -000
            "g293-s40",           # Base model
            "g293",               # Model family
        ]
        
        for pattern in search_patterns:
            if pattern in page_source:
                print(f"   ✅ Found pattern '{pattern}' in GPU-Server category")
            else:
                print(f"   ❌ Pattern '{pattern}' not found in GPU-Server category")
        
        print("\n📋 Test 3: Look for product links")
        links = driver.find_elements(By.TAG_NAME, "a")
        g293_links = []
        
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.text or ""
            
            if "g293" in href.lower() or "g293" in text.lower():
                g293_links.append({
                    "href": href,
                    "text": text.strip()
                })
        
        if g293_links:
            print(f"   ✅ Found {len(g293_links)} G293-related links:")
            for link in g293_links[:5]:  # Show first 5
                print(f"      • {link['text']} -> {link['href']}")
        else:
            print(f"   ❌ No G293-related links found")
        
        print("\n📋 Test 4: Navigate to specific product page")
        for link in g293_links:
            if "g293-s40" in link['href'].lower():
                print(f"   🎯 Found G293-S40 link: {link['href']}")
                driver.get(link['href'])
                time.sleep(3)
                print(f"   📄 Product page title: {driver.title}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    finally:
        driver.quit()

def main():
    """Main function"""
    print("Testing Search Methodology for Known G293-S40-AAP1")
    print("=" * 60)
    
    success = test_g293_search()
    
    if success:
        print(f"\n✅ Search methodology test completed")
    else:
        print(f"\n❌ Search methodology test failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
