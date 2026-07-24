import time
import requests
import os
from pathlib import Path

# En popüler 20 ülke ve aranacak merkez şehirler
TARGETS = {
    "france": "Paris",
    "italy": "Rome",
    "japan": "Tokyo",
    "turkey": "Istanbul",
    "spain": "Madrid",
    "germany": "Berlin",
    "greece": "Athens",
    "portugal": "Lisbon",
    "netherlands": "Amsterdam",
    "belgium": "Brussels",
    "switzerland": "Zurich",
    "austria": "Vienna",
    "czech_republic": "Prague",
    "hungary": "Budapest",
    "united_kingdom": "London",
    "united_states": "New York",
    "brazil": "Rio de Janeiro",
    "egypt": "Cairo",
    "thailand": "Bangkok",
    "australia": "Sydney"
}

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def fetch_places(city_name, node_type, limit=5):
    """Overpass API üzerinden belirli bir şehirdeki mekanları çeker."""
    query = f"""
    [out:json];
    area["name:en"="{city_name}"]->.searchArea;
    (
      node[{node_type}](area.searchArea);
      way[{node_type}](area.searchArea);
      relation[{node_type}](area.searchArea);
    );
    out center {limit};
    """
    
    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        places = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', tags.get('name:en', 'İsimsiz Mekan'))
            
            # Merkez koordinatları al
            if element['type'] == 'node':
                lat, lon = element['lat'], element['lon']
            elif 'center' in element:
                lat, lon = element['center']['lat'], element['center']['lon']
            else:
                continue
                
            if name != 'İsimsiz Mekan':
                places.append(f"{name} (Enlem: {lat}, Boylam: {lon})")
                
        return places
    except Exception as e:
        print(f"Hata ({city_name}, {node_type}): {e}")
        return []

def main():
    travel_data_dir = Path("travel_data")
    if not travel_data_dir.exists():
        print("travel_data klasörü bulunamadı!")
        return

    for country, city in TARGETS.items():
        print(f"Overpass API'den {city} ({country.upper()}) verileri çekiliyor...")
        
        # Müzeler
        museums = fetch_places(city, '"tourism"="museum"', limit=5)
        # Tarihi Mekanlar
        historical = fetch_places(city, '"historic"', limit=5)
        
        file_path = travel_data_dir / f"country_{country}.txt"
        
        if not file_path.exists():
            print(f"Uyarı: {file_path.name} bulunamadı, atlanıyor.")
            continue
            
        content_to_add = "\n\n## Gerçek Harita Koordinatlı Önemli Noktalar (Overpass API)\n"
        if museums:
            content_to_add += "\n### Müzeler:\n" + "\n".join([f"- [📍 {m}](https://www.google.com/maps/search/?api=1&query={m.split(' (')[0].replace(' ', '+')})" for m in museums])
        if historical:
            content_to_add += "\n### Tarihi Yerler:\n" + "\n".join([f"- [📍 {h}](https://www.google.com/maps/search/?api=1&query={h.split(' (')[0].replace(' ', '+')})" for h in historical])
            
        if museums or historical:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content_to_add)
            print(f"-> {country.upper()} başarıyla güncellendi.")
        
        # Rate limit yememek için kısa bir bekleme
        time.sleep(2)

if __name__ == "__main__":
    main()
