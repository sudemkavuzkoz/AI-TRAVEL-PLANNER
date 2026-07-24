import os
import sys
import importlib

ROOT = r"c:\Users\Sudem\Desktop\AI TRAVEL PLANNER"
sys.path.insert(0, ROOT)

print("Loading database module...")
db = importlib.import_module("database")
print("database path:", db.__file__)
print("Has add_favorite_country:", hasattr(db, "add_favorite_country"))
print("Has get_favorite_countries:", hasattr(db, "get_favorite_countries"))
print("Has save_trip_plan:", hasattr(db, "save_trip_plan"))
