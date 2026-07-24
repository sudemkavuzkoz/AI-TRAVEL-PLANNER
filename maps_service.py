import os
import requests
from urllib.parse import quote

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


def search_google_places(query, country=None, limit=6):
    if not GOOGLE_MAPS_API_KEY:
        return []

    search_query = f"{query} {country or ''}".strip()
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": search_query,
        "key": GOOGLE_MAPS_API_KEY,
        "language": "tr",
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    results = []
    for item in payload.get("results", [])[:limit]:
        location = item.get("geometry", {}).get("location", {})
        results.append({
            "place_id": item.get("place_id", ""),
            "name": item.get("name", "Bilinmeyen mekan"),
            "address": item.get("formatted_address", "Adres bilinmiyor"),
            "rating": item.get("rating"),
            "types": item.get("types", []),
            "lat": location.get("lat"),
            "lng": location.get("lng"),
            "maps_url": build_google_maps_url(item),
            "embed_url": build_embed_url(item),
        })
    return results


def build_google_maps_url(item):
    if item.get("place_id"):
        return f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={item['place_id']}"
    query = item.get("name", "")
    return f"https://www.google.com/maps/search/{quote(query)}"


def build_embed_url(item):
    query = item.get("name", "")
    return f"https://www.google.com/maps?q={quote(query)}"
