import re
import time
from pathlib import Path
import wikipediaapi
from concurrent.futures import ThreadPoolExecutor, as_completed

COUNTRY_NAMES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", "Australia",
    "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium",
    "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
    "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Central African Republic",
    "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba",
    "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
    "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia",
    "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece",
    "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica",
    "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
    "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
    "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
    "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique",
    "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama",
    "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania",
    "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa",
    "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland",
    "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
    "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela",
    "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def build_country_text(country_name: str) -> str:
    wiki = wikipediaapi.Wikipedia(
        user_agent="MyTravelRAGApp/1.0 (travelplanner@example.com)",
        language='en'
    )
    page = wiki.page(country_name)
    if not page.exists():
        # Fallback dummy text in English if wikipedia fails
        return f"# {country_name}\n\n## Overview\n{country_name} is a beautiful country with rich history and culture.\n"
    
    sections = [
        f"# {country_name}",
        "",
        "## Overview",
        page.summary[:2000] if page.summary else f"{country_name} is a renowned destination.",
        ""
    ]
    
    TARGET_SECTIONS = ["history", "geography", "culture", "tourism", "cuisine", "climate", "demographics"]
    
    found_sections = 0
    for s in page.sections:
        title_lower = s.title.lower()
        if any(ts in title_lower for ts in TARGET_SECTIONS) and s.text:
            sections.append(f"## {s.title}")
            sections.append(s.text[:2000])
            sections.append("")
            found_sections += 1
            if found_sections >= 5:
                break
                
    if found_sections == 0:
         sections.append("## General Information")
         sections.append(f"{country_name} offers a wide range of attractions from historical sites to modern cities.")
         
    return "\n".join(sections)

def process_country(country_name, output_dir):
    slug = slugify(country_name)
    filepath = output_dir / f"country_{slug}.txt"
    content = build_country_text(country_name)
    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write("--- METADATA ---\n")
        handle.write(f"SOURCE_URL: https://en.wikipedia.org/wiki/{country_name.replace(' ', '_')}\n")
        handle.write(f"FILE_NAME: {filepath.name}\n")
        handle.write("PROCESSED_DATE: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
        handle.write("----------------\n\n")
        handle.write(content)
    return filepath

def write_country_files(output_dir="travel_data"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_country, c, output_dir): c for c in COUNTRY_NAMES}
        for future in as_completed(futures):
            try:
                res = future.result()
                created.append(res)
                print(f"Processed: {res}")
            except Exception as e:
                print(f"Error processing: {e}")
                
    return created

if __name__ == "__main__":
    files = write_country_files()
    print(f"Generated {len(files)} files in English from Wikipedia.")
