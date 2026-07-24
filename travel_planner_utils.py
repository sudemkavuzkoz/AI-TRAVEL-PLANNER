import os
import urllib.parse
from typing import List, Dict, Any

COUNTRY_DATA = {
    "Italy": ["Rome", "Florence", "Venice", "Milan", "Naples", "Tuscany"],
    "France": ["Paris", "Lyon", "Nice", "Marseille", "Bordeaux", "Provence"],
    "Japan": ["Tokyo", "Kyoto", "Osaka", "Hakone", "Nara"],
    "Turkey": ["Istanbul", "Cappadocia", "Antalya", "Izmir", "Fethiye"],
    "Spain": ["Barcelona", "Madrid", "Valencia", "Seville", "Granada"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Cologne", "Bavaria"],
    "Greece": ["Athens", "Santorini", "Crete", "Mykonos", "Rhodes"],
    "Portugal": ["Lisbon", "Porto", "Algarve", "Sintra", "Madeira"],
    "Netherlands": ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Delft"],
    "Belgium": ["Brussels", "Bruges", "Ghent", "Antwerp", "Liege"],
    "Switzerland": ["Zurich", "Lucerne", "Zermatt", "Interlaken", "Geneva"],
    "Norway": ["Oslo", "Bergen", "Tromso", "Lofoten", "Alesund"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmo", "Uppsala", "Kiruna"],
    "Denmark": ["Copenhagen", "Aarhus", "Odense", "Bornholm", "Roskilde"],
    "Austria": ["Vienna", "Salzburg", "Innsbruck", "Graz", "Hallstatt"],
    "Poland": ["Warsaw", "Krakow", "Gdansk", "Wroclaw", "Zakopane"],
    "Czech Republic": ["Prague", "Brno", "Cesky Krumlov", "Olomouc", "Karlovy Vary"],
    "Hungary": ["Budapest", "Szeged", "Debrecen", "Pecs", "Lake Balaton"],
    "Romania": ["Bucharest", "Brasov", "Sibiu", "Cluj-Napoca", "Constanta"],
    "Bulgaria": ["Sofia", "Plovdiv", "Varna", "Burgas", "Veliko Tarnovo"],
    "Croatia": ["Zagreb", "Split", "Dubrovnik", "Rovinj", "Hvar"],
    "Slovenia": ["Ljubljana", "Bled", "Portoroz", "Piran", "Maribor"],
    "Slovakia": ["Bratislava", "Kosice", "High Tatras", "Presov", "Liptovsky Mikulas"],
    "Serbia": ["Belgrade", "Novi Sad", "Subotica", "Kragujevac", "Nis"],
    "Bosnia and Herzegovina": ["Sarajevo", "Mostar", "Banja Luka", "Trebinje", "Jajce"],
    "Albania": ["Tirana", "Durres", "Saranda", "Vlora", "Kruja"],
    "Argentina": ["Buenos Aires", "Mendoza", "Bariloche", "Ushuaia", "Patagonia"],
    "Brazil": ["Rio de Janeiro", "Sao Paulo", "Salvador", "Recife", "Brasilia"],
    "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Banff"],
    "United States": ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco"],
    "Mexico": ["Mexico City", "Cancun", "Guadalajara", "Oaxaca", "Puerto Vallarta"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Cairns"],
    "New Zealand": ["Auckland", "Queenstown", "Wellington", "Rotorua", "Christchurch"],
    "India": ["Delhi", "Mumbai", "Jaipur", "Goa", "Bangalore"],
    "Thailand": ["Bangkok", "Chiang Mai", "Phuket", "Krabi", "Pattaya"],
    "Vietnam": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hoi An", "Hue"],
    "Singapore": ["Singapore", "Marina Bay", "Sentosa", "Orchard Road", "Chinatown"],
    "Indonesia": ["Bali", "Jakarta", "Yogyakarta", "Bandung", "Lombok"],
    "Philippines": ["Manila", "Cebu", "Palawan", "Boracay", "Bohol"],
    "South Africa": ["Cape Town", "Johannesburg", "Durban", "Kruger", "Stellenbosch"],
    "Morocco": ["Marrakech", "Fes", "Casablanca", "Rabat", "Chefchaouen"],
    "Egypt": ["Cairo", "Luxor", "Aswan", "Alexandria", "Sharm El Sheikh"],
    "Kenya": ["Nairobi", "Mombasa", "Nakuru", "Naivasha", "Lamu"],
    "Nepal": ["Kathmandu", "Pokhara", "Lumbini", "Bhaktapur", "Chitwan"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah"],
}


def get_countries() -> List[str]:
    return sorted(COUNTRY_DATA.keys())


def get_places_for_country(country: str) -> List[Dict[str, Any]]:
    if not country:
        return []
    return [{"Place_Name": city, "City": city, "Country": country} for city in COUNTRY_DATA.get(country, [])]


def build_google_maps_url(place: Dict[str, Any]) -> str:
    if isinstance(place, str):
        q = place
    else:
        query = place.get("Place_Name") or ""
        city = place.get("City") or ""
        country = place.get("Country") or ""
        search_terms = [query, city, country]
        q = ", ".join([term for term in search_terms if term])
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(q)}"
