import scrapy
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import random
import re

class LocationSpider(scrapy.Spider):
    name = "myspider"
    start_urls = [
        'https://www.google.com/maps/search/wedding+venues+sydney+cbd?hl=en',
    ]

    def __init__(self, cap=None):
        self.chrome_options = uc.ChromeOptions()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.chrome_options.add_argument(f'user-agent={user_agent}')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-extensions')
        
        self.driver = uc.Chrome(options=self.chrome_options)
        
        self.cap = int(cap) if cap is not None else None
        self.results_count = 0
        self.unique_urls = set()

    def extract_city(self, url):
        # Extract city from the URL
        # Example: "wedding+venues+sydney+cbd" -> "sydney"
        match = re.search(r'wedding\+venues\+([^+]+)', url)
        if match:
            return match.group(1).lower()
        return None

    def parse(self, response):
        self.driver.get(response.url)
        
        # Extract city from the URL
        search_city = self.extract_city(response.url)
        
        # Wait for initial results
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'Nv2PK'))
        )

        # Find the scrollable container
        try:
            scrollable_element = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        except:
            scrollable_element = self.driver

        # Scroll and collect results
        max_attempts = 50  # Prevent infinite loop
        attempts = 0

        while (self.cap is None or self.results_count < self.cap) and attempts < max_attempts:
            # Find and process venues
            venues = self.driver.find_elements(By.CLASS_NAME, 'Nv2PK')
            
            for venue in venues:
                # Stop if cap is reached
                if self.cap is not None and self.results_count >= self.cap:
                    break
                
                try:
                    link_element = venue.find_element(By.CSS_SELECTOR, 'a[aria-label]')
                    url = link_element.get_attribute('href')

                    # Yield unique URLs with city information
                    if url and url not in self.unique_urls:
                        self.unique_urls.add(url)
                        yield {
                            'url': url,
                            'search_city': search_city
                        }
                        self.results_count += 1
                
                except Exception as e:
                    self.logger.error(f"Error processing venue: {str(e)}")
                    continue
            
            # Aggressive scrolling
            try:
                # Scroll down using Page Down key
                scrollable_element.send_keys(Keys.PAGE_DOWN)
                time.sleep(1)
                
                # JavaScript scroll
                self.driver.execute_script("arguments[0].scrollTop += arguments[0].clientHeight;", scrollable_element)
                time.sleep(1)
                
                attempts += 1
                
                # Check if new venues loaded
                new_venues = self.driver.find_elements(By.CLASS_NAME, 'Nv2PK')
                if len(new_venues) <= len(venues):
                    attempts += 5  # Increase attempts to exit if no new venues
            
            except Exception as e:
                self.logger.error(f"Scrolling error: {str(e)}")
                attempts += 1
        
        # Ensure driver closes
        self.driver.quit()

    def closed(self, reason):
        try:
            self.driver.quit()
        except:
            pass