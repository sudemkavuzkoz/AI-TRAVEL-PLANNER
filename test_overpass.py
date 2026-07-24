import requests
import json

def test_overpass():
    query = """
    [out:json];
    area["name:en"="Italy"]->.searchArea;
    (
      node["amenity"="restaurant"](area.searchArea);
    );
    out 5;
    """
    response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=10)
    print(response.status_code)
    try:
        print(json.dumps(response.json(), indent=2)[:500])
    except:
        print("Failed to parse JSON")

if __name__ == "__main__":
    test_overpass()
