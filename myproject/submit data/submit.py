import json
import requests

# Define your API endpoint
API_ENDPOINT = "http://localhost:5000/api/venues"  # Replace with your actual API URL

# Read the JSON file containing venue data
with open("../imagedownloader/output.json", "r") as f:
    venues = json.load(f)

# Function to submit venue data to the API
def submit_venue(venue):
    # Prepare the data according to the Mongoose model
    venue_data = {
        "name": venue.get("name"),
        "address": venue.get("address"),
        "email": venue.get("email", ""),  # Assuming email is optional; provide default if not present
        "phone": venue.get("phone", ""),  # Assuming phone is optional; provide default if not present
        "images": [venue.get("image_url")],  # Assuming only one image per venue; adjust if multiple images are needed
        "rating": float(venue.get("rating", 0)),  # Convert rating to float
        "reviews": int(venue.get("reviews", "0").replace(',', '')),  # Convert reviews to int after removing commas
        "category": venue.get("category", "Wedding venue"),  # Default category if not provided
        "hours": venue.get("hours", "")  # Assuming hours is optional; provide default if not present
    }

    # Validate required fields
    if not venue_data['name'] or not venue_data['address'] or not venue_data['email'] or not venue_data['phone']:
        print(f"Missing required fields for {venue['name']}. Skipping submission.")
        return

    try:
        # Send a POST request to the API with the venue data
        response = requests.post(API_ENDPOINT, json=venue_data)
        
        # Check for successful submission
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        print(f"Successfully submitted: {venue['name']}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error submitting {venue['name']}: {str(e)}")

# Iterate over each venue and submit it to the API
for venue in venues:
    submit_venue(venue)

print("\nAll submissions complete!")
