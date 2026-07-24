import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "travel_rag.db")

def clear_chunks_and_keep_history():
    print(f"Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get current counts
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    history_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM countries")
    countries_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM document_chunks")
    chunks_count = cursor.fetchone()[0]
    
    print(f"Before cleanup:")
    print(f" - chat_history: {history_count} records")
    print(f" - countries: {countries_count} records")
    print(f" - document_chunks: {chunks_count} records")
    
    print("Clearing old document_chunks...")
    cursor.execute("DELETE FROM document_chunks;")
    
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='document_chunks';")
    except Exception:
        pass
        
    conn.commit()
    conn.close()
    
    print("Chunks cleared successfully! Chat history is preserved.")
    print("You can now start app.py to re-embed the new English files.")

if __name__ == "__main__":
    clear_chunks_and_keep_history()
