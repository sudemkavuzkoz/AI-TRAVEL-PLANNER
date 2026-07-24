import requests
import json

def test_wikidata_restaurants():
    query = """
    SELECT ?itemLabel (count(?sitelink) as ?linkcount) WHERE {
      ?item wdt:P31/wdt:P279* wd:Q11707. # restaurant
      ?item wdt:P17 wd:Q38. # country Italy
      ?sitelink schema:about ?item.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } GROUP BY ?itemLabel ORDER BY DESC(?linkcount) LIMIT 5
    """
    url = "https://query.wikidata.org/sparql"
    headers = {
        "Accept": "application/json",
        "User-Agent": "TravelPlannerBot/1.0"
    }
    response = requests.get(url, params={'query': query}, headers=headers, timeout=10)
    print("Status:", response.status_code)
    try:
        data = response.json()
        for item in data['results']['bindings']:
            print("-", item['itemLabel']['value'])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_wikidata_restaurants()
