import requests
import json
import time

def test_nominatim():
    headers = {
        'User-Agent': 'AI-Travel-Planner-App/1.0 (sudem@example.com)'
    }
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': 'museum in Italy',
        'format': 'json',
        'limit': 5
    }
    response = requests.get(url, params=params, headers=headers)
    print(response.status_code)
    try:
        data = response.json()
        for item in data:
            print("-", item.get('name', ''), item.get('display_name', ''))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_nominatim()
