import sqlite3
import numpy as np
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
from embedding import create_embedding

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "travel_rag.db")

ISTANBUL_DATA_EN = """The ultimate cultural and historical landmarks in Istanbul, Turkey include:
1. Hagia Sophia (Ayasofya): A magnificent architectural marvel that served as a church, mosque, and museum, featuring breathtaking mosaics and a massive dome.
2. Blue Mosque (Sultanahmet Camii): Famous for its stunning blue Iznik tiles, six minarets, and classical Ottoman architecture.
3. Topkapi Palace (Topkapi Sarayi): The opulent residence of Ottoman sultans for centuries, featuring the Harem, Treasury, and stunning views of the Bosphorus.
4. Basilica Cistern (Yerebatan Sarnici): An eerie and atmospheric underground water reservoir from the Byzantine era, featuring Medusa head pillars.
5. Grand Bazaar (Kapalicarsi): One of the oldest and largest covered markets in the world, perfect for buying spices, carpets, jewelry, and Turkish delight.
6. Galata Tower (Galata Kulesi): A medieval stone tower in Karakoy offering panoramic 360-degree views of the Istanbul skyline and the Golden Horn.
7. Dolmabahce Palace: A stunning European-style palace on the Bosphorus strait, known for its massive crystal chandelier and luxurious design.
8. Istiklal Avenue and Taksim Square: The bustling, vibrant heart of modern Istanbul, filled with historical trams, cafes, art galleries, and street musicians.
9. Bosphorus Cruise: A must-do experience bridging Europe and Asia, passing by Ottoman mansions (Yalis), Maiden's Tower (Kiz Kulesi), and majestic bridges.
These locations offer the most comprehensive, beautiful, and rich cultural experience for anyone visiting Istanbul."""

def inject_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM document_chunks WHERE source LIKE '%istanbul_enriched%'")
    
    print("Creating English embedding for Istanbul...")
    vector = np.array(create_embedding(ISTANBUL_DATA_EN), dtype=np.float32)
    vector_bytes = vector.tobytes()
    
    # 199 = Istanbul, 176 = Turkey
    for c_id in [176, 199]:
        cursor.execute("SELECT MAX(chunk_index) FROM document_chunks WHERE country_id = ?", (c_id,))
        max_idx = cursor.fetchone()[0]
        new_idx = (max_idx or 0) + 1
        
        cursor.execute("""
            INSERT INTO document_chunks (country_id, source, chunk_index, chunk_text, embedding)
            VALUES (?, ?, ?, ?, ?)
        """, (c_id, "istanbul_enriched", new_idx, ISTANBUL_DATA_EN, vector_bytes))
        
    conn.commit()
    conn.close()
    print("Istanbul cultural data successfully added to the RAG database!")

if __name__ == "__main__":
    inject_data()
