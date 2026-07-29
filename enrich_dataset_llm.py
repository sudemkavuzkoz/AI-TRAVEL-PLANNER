import os
import time
from pathlib import Path
from model import generate_response

def get_country_name(filepath):
    # Try reading the first few lines to find "# Country Name"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("# ") and "Country" not in line:
                    return line.replace("# ", "").strip()
    except:
        pass
    # Fallback to filename parsing
    name = filepath.stem.replace("country_", "").replace("_", " ").title()
    return name

def enrich_file(filepath):
    country = get_country_name(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "Famous Museums" in content or "## Restaurants" in content:
        # Already enriched
        return False
        
    prompt = f"List 5 famous real holiday destinations or coastal towns, 5 famous real museums, and 5 famous real local desserts in {country}. Use bullet points and group them under '## Famous Holiday Destinations', '## Famous Museums', and '## Local Desserts'. Do not add conversational intro/outro text. Write ONLY the requested sections in English."
    sys_prompt = "You are a helpful travel data assistant. Give concise bullet points. Output only the requested sections."
    
    print(f"Generating data for {country}...")
    response = generate_response(prompt, sys_prompt)
    
    if response and "Yanıt Üretilemedi" not in response and "Error" not in response:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write("\n\n" + response + "\n")
        print(f" -> Enriched {country}")
        return True
    else:
        print(f" -> Failed to generate for {country}")
        return False

def main():
    data_dir = Path("travel_data")
    if not data_dir.exists():
        print("travel_data directory not found.")
        return
        
    files = list(data_dir.glob("country_*.txt"))
    total = len(files)
    count = 0
    
    print(f"Found {total} files to process.")
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{total}] Processing {file_path.name}")
        success = enrich_file(file_path)
        if success:
            count += 1
            
    print(f"Enriched {count} files successfully.")
    
if __name__ == "__main__":
    main()
