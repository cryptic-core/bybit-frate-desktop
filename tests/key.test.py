import json
import unittest
from requests import post  # Import the post method from requests

# Replace with the actual URL of your running FastAPI application
API_URL = "https://bybit-frate-desktop-production.up.railway.app/key"

class TestAPI(unittest.TestCase):

    def test_post_key(self):
        # Prepare the data to send in the POST request
        data = {
            "apikey": "your_api_key",
            "secretkey": "your_secret_key",
            "timestamp": "2024-04-19T08:30:00Z"  # Example timestamp (replace with your actual format)
        }
        # Send the POST request and get the response
        response = post(API_URL, json=data)

        # Assert the expected status code (200 for success)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.text)
        #print(f'the resp message: {response_data["message"]}')
        self.assertEqual(response_data["message"], "Data received successfully!")  # Replace assertion based on your response

if __name__ == "__main__":
    unittest.main()
