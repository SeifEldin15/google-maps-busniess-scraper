import json
import os
import requests
from urllib.parse import urlparse
import re

# Function to clean the address field
def clean_address(address):
    """
    Cleans the address by removing unwanted or non-ASCII characters.
    """
    if not address:
        return address  # Return as is if None or empty
    # Remove non-ASCII characters and strip whitespace
    return re.sub(r'[^\x20-\x7E]', '', address).strip()

# Create images directory if it doesn't exist
IMAGES_DIR = "venue_images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Read the JSON file
with open("../../venue_details.json", "r") as f:
    venues = json.load(f)

# List to hold updated venue data
updated_venues = []

# Download images for each venue
for venue in venues:
    try:
        # Clean the address field
        if 'address' in venue and venue['address']:
            venue['address'] = clean_address(venue['address'])

        # Check if 'image_url' exists in the venue
        if 'image_url' not in venue or not venue['image_url']:
            print("No image URL found for a venue. Skipping...")
            updated_venues.append(venue)  # Keep original data if no image
            continue
        
        # Get the image URL
        image_url = venue['image_url']
        
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Determine file extension from content type
        content_type = response.headers.get('Content-Type')
        if content_type:
            extension = content_type.split('/')[-1]  # Get the last part after '/'
            if extension in ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'webp']:
                original_filename = f"{os.path.basename(urlparse(image_url).path)}.{extension}"
            else:
                original_filename = os.path.basename(urlparse(image_url).path)
        else:
            original_filename = os.path.basename(urlparse(image_url).path)

        # Create the file path
        filepath = os.path.join(IMAGES_DIR, original_filename)
        
        # Save the image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {original_filename}")
        
        # Update the venue's image_url to the new filename
        venue['image_url'] = original_filename
    
    except Exception as e:
        print(f"Error downloading image from {venue.get('image_url', 'Unknown URL')}: {str(e)}")
        updated_venues.append(venue)  # Keep original data in case of error
        continue

    # Append updated venue data to list
    updated_venues.append(venue)

# Write updated venues to a new JSON file
with open("output.json", "w") as f:
    json.dump(updated_venues, f, indent=4)

print("\nDownload complete! Updated output written to output.json.")
