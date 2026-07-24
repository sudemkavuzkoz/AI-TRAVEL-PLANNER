import requests
import json

def test_overpass_raw_post():
    query = """
    [out:json];
    area["name:en"="Italy"]->.searchArea;
    (
      node["amenity"="restaurant"](area.searchArea);
    );
    out center 5;
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": "TravelPlannerBot/1.0"
    }
    response = requests.post("https://overpass-api.de/api/interpreter", data=query, headers=headers)
    print("Status:", response.status_code)
    try:
        data = response.json()
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            print(f"- {tags.get('name', 'Unknown')}")
    except Exception as e:
        print("Error parsing JSON:", e)

if __name__ == "__main__":
    test_overpass_raw_post()
