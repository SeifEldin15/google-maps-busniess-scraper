import json
import os
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import re

class VenueDetailScraper:
    def __init__(self):
        # Chrome options to avoid detection
        self.chrome_options = uc.ChromeOptions()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.chrome_options.add_argument(f'user-agent={user_agent}')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-extensions')
        
        # Initialize driver
        self.driver = uc.Chrome(options=self.chrome_options)
    
    def clean_text(self, text):
        """Clean text by removing extra whitespace and newlines"""
        if text and isinstance(text, str):
            # Replace newlines with spaces and remove extra whitespace
            cleaned = ' '.join(text.split())
            return cleaned
        return text

    def scrape_venue_details(self, url_data):
        venue_details = []
        
        for item in url_data:
            url = item['url']
            city = item['search_city']
            
            try:
                # Navigate to the URL
                self.driver.get(url)
                
                # Wait for main content to load
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h1'))
                )
                
                # Random wait to mimic human behavior
                time.sleep(random.uniform(2, 5))
                
                # Extract venue name
                try:
                    venue_name = self.clean_text(self.driver.find_element(By.CSS_SELECTOR, 'h1').text)
                except:
                    venue_name = "N/A"
                
                # Extract address
                try:
                    address = self.clean_text(self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]').text)
                except:
                    address = "N/A"
                
                # Extract phone number
                try:
                    phone_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^="phone:tel:"]')
                    phone = phone_button.text
                    
                    if not phone:
                        phone = phone_button.get_attribute('aria-label')
                    
                    phone = re.sub(r'[^\d+\-() ]', '', phone)
                    phone = self.clean_text(phone)
                    
                    if not any(char.isdigit() for char in phone):
                        phone = "N/A"
                except:
                    phone = "N/A"
                
                # Extract website
                try:
                    website = self.driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]').get_attribute('href')
                except:
                    website = "N/A"
                
                # Extract rating and reviews
                try:
                    rating_reviews_element = self.driver.find_element(By.CSS_SELECTOR, '.F7nice')
                    rating = self.clean_text(rating_reviews_element.find_element(By.CSS_SELECTOR, 'span[aria-hidden="true"]').text)
                    reviews_element = rating_reviews_element.find_element(By.CSS_SELECTOR, 'span[aria-label$="reviews"]')
                    reviews = re.findall(r'\d+', reviews_element.get_attribute('aria-label'))[0]
                except:
                    rating = "N/A"
                    reviews = "0"
                
                # Extract main image URL
                try:
                    image_elements = self.driver.find_elements(By.CSS_SELECTOR, 'button.aoRNLd img')
                    if not image_elements:
                        image_elements = self.driver.find_elements(By.CSS_SELECTOR, 'button[jsaction*="heroHeaderImage"] img')
                    
                    if image_elements:
                        image_url = image_elements[0].get_attribute('src')
                    else:
                        image_url = "N/A"
                except:
                    image_url = "N/A"
                
                # Extract category
                try:
                    category_selectors = [
                        'button.DkEaL',
                        'button[jsaction*="category"]',
                        'button[jsaction="pane.rating.category"]'
                    ]
                    
                    categories = []
                    for selector in category_selectors:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            text = self.clean_text(elem.text)
                            if text and text not in categories:
                                categories.append(text)
                    
                    category = ' • '.join(categories) if categories else "N/A"
                except:
                    category = "N/A"
                
                # Extract email
                try:
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    email_matches = re.findall(email_pattern, page_text)
                    email = email_matches[0] if email_matches else "N/A"
                    
                    if email == "N/A":
                        email_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href^="mailto:"]')
                        if email_elements:
                            email = email_elements[0].get_attribute('href').replace('mailto:', '')
                except:
                    email = "N/A"
        # Extract working hours
                try:
                    # Locate the working hours container using the provided class
                    working_hours_container = self.driver.find_element(By.CLASS_NAME, 'ZDu9vd')
                    
                    # Extract the full working hours text (assumes a single container with "Open 24 hours" or similar)
                    working_hours_text = self.clean_text(working_hours_container.text)
                    
                    # Set the "hours" key directly with the extracted text
                    if working_hours_text:
                        hours = working_hours_text
                    else:
                        hours = "N/A"  # Default if no text is found
                except Exception as e:
                    print(f"Failed to extract working hours: {str(e)}")
                    hours = "N/A"
                
                # Compile venue details with city
                venue_info = {
                    'name': venue_name,
                    'address': address,
                    'phone': phone,
                    'website': website,
                    'email': email,
                    'category': category,
                    'image_url': image_url,
                    'rating': rating,
                    'reviews': reviews,
                    'original_url': url,
                    'search_city': city,
                    'hours': hours  # Include the hours here
                }
                venue_details.append(venue_info)
                
                # Random wait between requests
                time.sleep(random.uniform(1, 3))
            
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
        
        return venue_details
    
    def save_to_json(self, venue_details, filename='venue_details.json'):
        with open(filename, 'w', encoding='utf-8') as output_file:
            json.dump(venue_details, output_file, indent=2, ensure_ascii=False)
    
    def close(self):
        self.driver.quit()

def main():
    input_file = 'output.json'
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please ensure the file exists in the current directory.")
        return
        
    # Check if file is empty
    if os.path.getsize(input_file) == 0:
        print(f"Error: {input_file} is empty.")
        return
        
    try:
        # Load URLs and cities from the previous scraping result
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                url_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in {input_file}")
                print(f"Details: {str(e)}")
                return
                
        # Verify the data structure
        if not isinstance(url_data, list):
            print(f"Error: Expected a list in {input_file}, but got {type(url_data)}")
            return
            
        if not url_data:
            print(f"Error: No data found in {input_file}")
            return
            
        # Check if the required fields are present
        for item in url_data:
            if not isinstance(item, dict):
                print(f"Error: Expected dictionary items in {input_file}, but got {type(item)}")
                return
            if 'url' not in item:
                print(f"Error: Missing 'url' field in item: {item}")
                return
            if 'search_city' not in item:
                print(f"Error: Missing 'search_city' field in item: {item}")
                return
        
        # Initialize and run scraper
        scraper = VenueDetailScraper()
        try:
            venue_details = scraper.scrape_venue_details(url_data)
            scraper.save_to_json(venue_details)
            print(f"Scraped {len(venue_details)} venues successfully!")
        finally:
            scraper.close()
            
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return

if __name__ == "__main__":
    main()