import sqlite3
import numpy as np
import os
import sys

# Windows Unicode output fix
sys.stdout.reconfigure(encoding='utf-8')

from embedding import create_embedding

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "travel_rag.db")

BEACH_DATA_EN = """The most famous and beautiful beaches in Turkey are:
1. Kaputas Beach: A unique beach with turquoise water located in Kas, Antalya.
2. Lara Beach: A very popular wide sandy beach close to the city center of Antalya.
3. Konyaalti Beach: A magnificent beach with mountain views in the center of Antalya.
4. Iztuzu Beach: A wonderful natural wonder where Caretta caretta turtles lay their eggs in Dalyan, Mugla.
5. Patara Beach: A famous beach with endless sand dunes next to the ancient city near Kalkan, Antalya.
6. Oludeniz (Blue Lagoon): A unique lagoon located in Fethiye, Mugla, chosen as one of the most beautiful beaches in the world.
7. Cirali and Olympos Beach: A peaceful coast intertwined with pine forests in Antalya.
8. Cleopatra Beach: A famous beach with golden sand located in Alanya, Antalya.
These beaches are the most touristic, beautiful, and Blue Flag awarded beaches in Turkey."""

def inject_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Delete the Turkish version that was added recently
    cursor.execute("DELETE FROM document_chunks WHERE source LIKE '%(AI Enriched)%'")
    
    print("Creating English embedding...")
    vector = np.array(create_embedding(BEACH_DATA_EN), dtype=np.float32)
    vector_bytes = vector.tobytes()
    
    # 176 = Turkey, 195 = Antalya
    for c_id in [176, 195]:
        cursor.execute("SELECT MAX(chunk_index) FROM document_chunks WHERE country_id = ?", (c_id,))
        max_idx = cursor.fetchone()[0]
        new_idx = (max_idx or 0) + 1
        
        cursor.execute("""
            INSERT INTO document_chunks (country_id, source, chunk_index, chunk_text, embedding)
            VALUES (?, ?, ?, ?, ?)
        """, (c_id, "country_turkey.txt (AI Enriched)", new_idx, BEACH_DATA_EN, vector_bytes))
        
    conn.commit()
    conn.close()
    print("English beach data successfully added to the RAG database!")

if __name__ == "__main__":
    inject_data()
