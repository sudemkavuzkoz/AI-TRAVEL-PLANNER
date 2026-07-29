"""
enrich_with_wikipedia.py
========================
Finds all country_*.txt files in the travel_data folder,
fetches the English Wikipedia page for each, and APPENDS it to the file.
It does NOT touch the existing content.
In the final step, it re-embeds all files to update the RAG database.
"""

import os
import glob
import time
import sys

# --- Wikipedia API ile veri çekme ---
try:
    import wikipediaapi
except ImportError:
    print("❌ 'wikipediaapi' library not found! To install: pip install wikipedia-api")
    sys.exit(1)

from embedding import create_embeddings, _get_model
from database import init_db, insert_document

DATA_DIR = "travel_data"
# Dictionary mapping country file names to English Wikipedia page titles.
# We are also directing English file names to the correct Wikipedia page.
COUNTRY_NAME_MAP = {
    # Turkish Tourist Cities
    "antalya": "Antalya",
    "istanbul": "Istanbul",
    "izmir": "İzmir",
    "bodrum": "Bodrum",
    "fethiye": "Fethiye",
    "cappadocia": "Cappadocia",
    "marmaris": "Marmaris",
    "alanya": "Alanya",
    # Türkçe dosya adları
    "turkiye": "Türkiye",
    "almanya": "Almanya",
    "fransa": "Fransa",
    "italya": "İtalya",
    "japonya": "Japonya",
    "ispanya": "İspanya",
    "isvicre": "İsviçre",
    "kanada": "Kanada",
    "fas": "Fas",
    "guney_afrika": "Güney Afrika Cumhuriyeti",
    "filipinler": "Filipinler",
    "yeni_zelanda": "Yeni Zelanda",
    "norveç": "Norveç",
    "yunanistan": "Yunanistan",
    # İngilizce dosya adları
    "afghanistan": "Afganistan",
    "albania": "Arnavutluk",
    "algeria": "Cezayir",
    "andorra": "Andorra",
    "angola": "Angola",
    "antigua_and_barbuda": "Antigua ve Barbuda",
    "argentina": "Arjantin",
    "armenia": "Ermenistan",
    "australia": "Avustralya",
    "austria": "Avusturya",
    "azerbaijan": "Azerbaycan",
    "bahamas": "Bahamalar",
    "bahrain": "Bahreyn",
    "bangladesh": "Bangladeş",
    "barbados": "Barbados",
    "belarus": "Belarus",
    "belgium": "Belçika",
    "belize": "Belize",
    "benin": "Benin",
    "bhutan": "Bhutan",
    "bolivia": "Bolivya",
    "bosnia_and_herzegovina": "Bosna-Hersek",
    "botswana": "Botsvana",
    "brazil": "Brezilya",
    "brunei": "Brunei",
    "bulgaria": "Bulgaristan",
    "burkina_faso": "Burkina Faso",
    "burundi": "Burundi",
    "cabo_verde": "Yeşil Burun Adaları",
    "cape_verde": "Yeşil Burun Adaları",
    "cambodia": "Kamboçya",
    "cameroon": "Kamerun",
    "canada": "Kanada",
    "central_african_republic": "Orta Afrika Cumhuriyeti",
    "chad": "Çad",
    "chile": "Şili",
    "china": "Çin",
    "colombia": "Kolombiya",
    "comoros": "Komorlar",
    "congo": "Kongo Cumhuriyeti",
    "costa_rica": "Kosta Rika",
    "croatia": "Hırvatistan",
    "cuba": "Küba",
    "cyprus": "Kıbrıs",
    "czech_republic": "Çekya",
    "denmark": "Danimarka",
    "djibouti": "Cibuti",
    "dominica": "Dominika",
    "dominican_republic": "Dominik Cumhuriyeti",
    "ecuador": "Ekvador",
    "egypt": "Mısır",
    "el_salvador": "El Salvador",
    "equatorial_guinea": "Ekvator Ginesi",
    "eritrea": "Eritre",
    "estonia": "Estonya",
    "eswatini": "Esvatini",
    "ethiopia": "Etiyopya",
    "fiji": "Fiji",
    "finland": "Finlandiya",
    "france": "Fransa",
    "gabon": "Gabon",
    "gambia": "Gambiya",
    "georgia": "Gürcistan",
    "germany": "Almanya",
    "ghana": "Gana",
    "greece": "Yunanistan",
    "grenada": "Grenada",
    "guatemala": "Guatemala",
    "guinea": "Gine",
    "guinea_bissau": "Gine-Bissau",
    "guyana": "Guyana",
    "haiti": "Haiti",
    "honduras": "Honduras",
    "hungary": "Macaristan",
    "iceland": "İzlanda",
    "india": "Hindistan",
    "indonesia": "Endonezya",
    "iran": "İran",
    "iraq": "Irak",
    "ireland": "İrlanda",
    "israel": "İsrail",
    "italy": "İtalya",
    "jamaica": "Jamaika",
    "japan": "Japonya",
    "jordan": "Ürdün",
    "kazakhstan": "Kazakistan",
    "kenya": "Kenya",
    "kiribati": "Kiribati",
    "kuwait": "Kuveyt",
    "kyrgyzstan": "Kırgızistan",
    "laos": "Laos",
    "latvia": "Letonya",
    "lebanon": "Lübnan",
    "lesotho": "Lesotho",
    "liberia": "Liberya",
    "libya": "Libya",
    "liechtenstein": "Lihtenştayn",
    "lithuania": "Litvanya",
    "luxembourg": "Lüksemburg",
    "madagascar": "Madagaskar",
    "malawi": "Malavi",
    "malaysia": "Malezya",
    "maldives": "Maldivler",
    "mali": "Mali",
    "malta": "Malta",
    "marshall_islands": "Marshall Adaları",
    "mauritania": "Moritanya",
    "mauritius": "Mauritius",
    "mexico": "Meksika",
    "micronesia": "Mikronezya Federal Devletleri",
    "moldova": "Moldova",
    "monaco": "Monako",
    "mongolia": "Moğolistan",
    "montenegro": "Karadağ",
    "morocco": "Fas",
    "mozambique": "Mozambik",
    "myanmar": "Myanmar",
    "namibia": "Namibya",
    "nauru": "Nauru",
    "nepal": "Nepal",
    "netherlands": "Hollanda",
    "new_zealand": "Yeni Zelanda",
    "nicaragua": "Nikaragua",
    "niger": "Nijer",
    "nigeria": "Nijerya",
    "north_korea": "Kuzey Kore",
    "north_macedonia": "Kuzey Makedonya",
    "norway": "Norveç",
    "oman": "Umman",
    "pakistan": "Pakistan",
    "palau": "Palau",
    "panama": "Panama",
    "papua_new_guinea": "Papua Yeni Gine",
    "paraguay": "Paraguay",
    "peru": "Peru",
    "philippines": "Filipinler",
    "poland": "Polonya",
    "portugal": "Portekiz",
    "qatar": "Katar",
    "romania": "Romanya",
    "russia": "Rusya",
    "rwanda": "Ruanda",
    "saint_kitts_and_nevis": "Saint Kitts ve Nevis",
    "saint_lucia": "Saint Lucia",
    "saint_vincent_and_the_grenadines": "Saint Vincent ve Grenadinler",
    "samoa": "Samoa",
    "san_marino": "San Marino",
    "sao_tome_and_principe": "São Tomé ve Príncipe",
    "saudi_arabia": "Suudi Arabistan",
    "senegal": "Senegal",
    "serbia": "Sırbistan",
    "seychelles": "Seyşeller",
    "sierra_leone": "Sierra Leone",
    "singapore": "Singapur",
    "slovakia": "Slovakya",
    "slovenia": "Slovenya",
    "solomon_islands": "Solomon Adaları",
    "somalia": "Somali",
    "south_africa": "Güney Afrika Cumhuriyeti",
    "south_korea": "Güney Kore",
    "south_sudan": "Güney Sudan",
    "spain": "İspanya",
    "sri_lanka": "Sri Lanka",
    "sudan": "Sudan",
    "suriname": "Surinam",
    "sweden": "İsveç",
    "switzerland": "İsviçre",
    "syria": "Suriye",
    "taiwan": "Tayvan",
    "tajikistan": "Tacikistan",
    "tanzania": "Tanzanya",
    "thailand": "Tayland",
    "timor_leste": "Doğu Timor",
    "togo": "Togo",
    "tonga": "Tonga",
    "trinidad_and_tobago": "Trinidad ve Tobago",
    "tunisia": "Tunus",
    "turkey": "Türkiye",
    "turkmenistan": "Türkmenistan",
    "tuvalu": "Tuvalu",
    "uganda": "Uganda",
    "ukraine": "Ukrayna",
    "united_arab_emirates": "Birleşik Arap Emirlikleri",
    "united_kingdom": "Birleşik Krallık",
    "united_states": "Amerika Birleşik Devletleri",
    "uruguay": "Uruguay",
    "uzbekistan": "Özbekistan",
    "vanuatu": "Vanuatu",
    "vatican_city": "Vatikan",
    "venezuela": "Venezuela",
    "vietnam": "Vietnam",
    "yemen": "Yemen",
    "zambia": "Zambiya",
    "zimbabwe": "Zimbabve",
}

# Gereksiz bölümleri filtrele
IGNORE_SECTIONS = ["references", "external links", "see also", "notes", "bibliography"]

# Başlıkta bu kelimeler varsa o bölümü ve alt bölümlerini atla
IGNORE_SECTION_TITLES_CONTAINING = ["gallery", "citations"]

def should_keep_section(title):
    return not any(ignore in title.lower() for ignore in IGNORE_SECTIONS)


def extract_sections_recursive(sections, blocks):
    """Wikipedia bölümlerini özyinelemeli olarak çeker."""
    for section in sections:
        if should_keep_section(section.title):
            # Eğer bölüm başlığı "Gallery" gibi istenmeyen bir kelime içeriyorsa, bu bölümü ve altındakileri atla
            if any(word in section.title.lower() for word in IGNORE_SECTION_TITLES_CONTAINING):
                continue
            if section.text.strip():
                blocks.append(f"## {section.title}\n{section.text.strip()}\n")
            if section.sections:
                extract_sections_recursive(section.sections, blocks)


def fetch_wikipedia_content(page_title):
    """Fetches the content of a country page from English Wikipedia."""
    wiki = wikipediaapi.Wikipedia(
        user_agent="AITravelPlannerRAG/2.0 (travelplanner@example.com)",
        language="en" # Dili İngilizce olarak değiştir
    )
    page = wiki.page(page_title)
    if not page.exists():
        return None

    blocks = []
    # Summary
    if page.summary.strip():
        blocks.append(f"## Summary\n{page.summary.strip()}\n")

    # All sections
    extract_sections_recursive(page.sections, blocks)

    return "\n".join(blocks)


def chunk_text(text, chunk_size=500):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size
    return chunks


def read_file_content(filepath):
    """Reads the entire current content of the file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"  ⚠️ File could not be read: {e}")
        return ""


def main():
    print("=" * 60)
    print("🌍 DATASET ENRICHMENT WITH WIKIPEDIA & EMBEDDING")
    print("=" * 60)

    # 1. ADIM: Tüm country_*.txt dosyalarını bul
    pattern = os.path.join(DATA_DIR, "country_*.txt")
    country_files = sorted(glob.glob(pattern))
    total = len(country_files)
    print(f"\n📂 Found a total of {total} country files.\n")

    if total == 0:
        print("❌ No country_*.txt files found!")
        return

    # 2. ADIM: Her dosya için Wikipedia verisini çek ve dosyanın sonuna ekle
    enriched_count = 0
    skipped_count = 0

    for i, filepath in enumerate(country_files, 1):
        filename = os.path.basename(filepath)
        # country_almanya.txt -> almanya
        country_key = filename.replace("country_", "").replace(".txt", "")

        wiki_title = COUNTRY_NAME_MAP.get(country_key)
        if not wiki_title:
            print(f"  [{i}/{total}] ⏭️  Skipped (no match found): {filename}")
            skipped_count += 1
            continue

        # Dosyada zaten Wikipedia verisi var mı kontrol et
        existing_content = read_file_content(filepath)
        if "## 📖 Wikipedia Information" in existing_content:
            print(f"  [{i}/{total}] ✅ Already enriched: {filename}")
            skipped_count += 1
            continue

        print(f"  [{i}/{total}] 🔄 Fetching Wikipedia: '{wiki_title}' -> {filename}")

        wiki_content = fetch_wikipedia_content(wiki_title)
        if not wiki_content or len(wiki_content) < 100:
            print(f"           ⚠️ Wikipedia content insufficient or not found.")
            skipped_count += 1
            continue

        # Mevcut dosyanın SONUNA ekleme yap (mevcut içeriğe dokunma!)
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write("\n\n")
                f.write("=" * 50 + "\n")
                f.write(f"## 📖 Wikipedia Information — {wiki_title}\n")
                f.write(f"SOURCE_URL: https://en.wikipedia.org/wiki/{wiki_title.replace(' ', '_')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(wiki_content)
            enriched_count += 1
            print(f"           ✅ Added! (+{len(wiki_content)} characters)")
        except Exception as e:
            print(f"           ❌ Write error: {e}")

        # Wikipedia API'yi yormamak için kısa bekleme
        time.sleep(0.3)

    print(f"\n{'=' * 60}")
    print(f"📊 Zenginleştirme Özeti: {enriched_count} dosya güncellendi, {skipped_count} atlandı")
    print(f"{'=' * 60}")

    # 3. ADIM: Tüm dosyaları yeniden embedding yap
    print(f"\n🧠 Starting embedding process...\n")
    _get_model()

    start_time = time.time()
    conn = init_db()

    # Mevcut document kayıtlarını temizle (temiz yeniden indeksleme)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents")
    conn.commit()
    print("🗑️  Old embedding records have been cleared.")

    all_chunks = []
    txt_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")))

    for i, filepath in enumerate(txt_files, 1):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Metadata bloğunu ayır
            parts = content.split("----------------", 1)
            if len(parts) == 2:
                metadata_block = parts[0]
                text = parts[1].strip()
                source_url = os.path.basename(filepath)
                for line in metadata_block.split("\n"):
                    if line.strip().startswith("SOURCE_URL:"):
                        source_url = line.split("SOURCE_URL:", 1)[1].strip()
                        break
            else:
                text = content.strip()
                source_url = os.path.basename(filepath)

            if not text:
                continue

            chunks = chunk_text(text)
            for chunk in chunks:
                all_chunks.append((source_url, chunk))

            if i % 50 == 0 or i == len(txt_files):
                print(f"  Read: {i}/{len(txt_files)} files...")
        except Exception as e:
            print(f"  ⚠️ Read error ({os.path.basename(filepath)}): {e}")
            continue

    print(f"\n📊 A total of {len(all_chunks)} text chunks are ready. Generating embeddings...")

    texts = [chunk for _, chunk in all_chunks]
    sources = [src for src, _ in all_chunks]

    # Batch halinde embedding üret (bellek dostu)
    BATCH_SIZE = 256
    all_embeddings = []
    for batch_start in range(0, len(texts), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(texts))
        batch_texts = texts[batch_start:batch_end]
        batch_embeddings = create_embeddings(batch_texts)
        all_embeddings.extend(batch_embeddings)
        print(f"  ⚡ Embedding: {batch_end}/{len(texts)} completed")

    print("💾 Saving to database...")
    for source, chunk, emb in zip(sources, texts, all_embeddings):
        insert_document(conn, source, chunk, emb)

    conn.commit()
    conn.close()

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"🎉 COMPLETED!")
    print(f"   📄 {len(txt_files)} files processed")
    print(f"   🧩 {len(all_chunks)} text chunks embedded")
    print(f"   ⏱️  Duration: {elapsed:.1f} seconds")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
