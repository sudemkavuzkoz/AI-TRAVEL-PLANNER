import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from travel_planner_utils import get_countries, get_places_for_country, build_google_maps_url


def test_country_and_places_catalog():
    countries = get_countries()
    assert "Italy" in countries
    italy_places = get_places_for_country("Italy")
    assert len(italy_places) > 0
    assert any(place["Place_Name"] == "Colosseum" for place in italy_places)


def test_google_maps_url_generation():
    place = {"Place_Name": "Colosseum", "City": "Rome", "Country": "Italy"}
    url = build_google_maps_url(place)
    assert "google.com/maps" in url
    assert "Colosseum" in url
